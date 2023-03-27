import abc
import copy
from decimal import Decimal

from api.globals.carriers import CAN_NORTH
from api.models import SkylineAccount
from brain.settings import SKYLINE_BASE_URL


class SkylineAPI(abc.ABC):
    """
    Parent class to all skyline API.
    """

    _northern_tax_rate = Decimal("0.05")
    _dim_factor = Decimal("6000.00")
    _sig_fig = Decimal("0.01")
    _hundred = Decimal("100.00")

    _rate_url = SKYLINE_BASE_URL + "/Rate/GetRate"
    _track_url = SKYLINE_BASE_URL + "/LegacyTrackAndTrace/TrackAndTrace"
    _ship_url = SKYLINE_BASE_URL + "/Ship/Ship"
    _awb_url = SKYLINE_BASE_URL + "/Reports/Waybill"
    _rated_awb_url = SKYLINE_BASE_URL + "/Reports/RatedWaybill"
    _cargo_labels_url = SKYLINE_BASE_URL + "/Reports/CargoLabels"

    def __init__(self, gobox_request: dict) -> None:
        self._gobox_request = copy.deepcopy(gobox_request)
        self._is_delivery = self._gobox_request.get("is_delivery", False)
        self._is_pickup = self._gobox_request.get("is_pickup", False)
        self._is_food = gobox_request.get("is_food", False)
        self._sub_account = self._gobox_request["objects"]["sub_account"]
        self._total_packages = 0
        self._total_weight = Decimal("0.00")
        self._total_dim = Decimal("0.00")
        self._processed_packages = []

    @abc.abstractmethod
    def _build(self) -> None:
        pass

    @abc.abstractmethod
    def _format_response(self):
        pass

    @abc.abstractmethod
    def _post(self, data: dict):
        pass

    def _rate_priorities(self):
        """
        Gets the Skyline Account and corresponding Nature of Goods for the account
        """
        carrier_account = self._gobox_request["objects"]["carrier_accounts"][CAN_NORTH][
            "account"
        ]

        accounts = SkylineAccount.objects.prefetch_related("nog_account").filter(
            sub_account=carrier_account.subaccount
        )

        account = accounts.first()

        self._api_key = carrier_account.api_key.decrypt()
        self._skyline_account = account
        self._nature_of_goods = account.nog_account.filter(is_food=self._is_food)

    def _process_packages(self):
        """
        Process GoBox request packages into Skyline packages. It also gets the total weight, total packages, and
        total dimensional.
        """
        # TODO : REMOVE is_cooler and is_frozen, makes no sense

        packages = self._gobox_request["packages"]

        for package in packages:
            is_dangerous = False
            is_envelope = False
            quantity = Decimal(package["quantity"])
            length = Decimal(package["length"]).quantize(self._sig_fig)
            width = Decimal(package["width"]).quantize(self._sig_fig)
            height = Decimal(package["height"])
            weight = Decimal(package["weight"])
            un_number = package.get("un_number", 0)

            if un_number is not None and un_number != 0:
                is_dangerous = True

            if weight < Decimal("1"):
                weight = Decimal("1")

            if weight < Decimal("2"):
                is_envelope = True

            weight_quantity = (weight * quantity).quantize(self._sig_fig)
            height_quantity = (height * quantity).quantize(self._sig_fig)
            dim_weight = (
                ((length * width * height) / self._dim_factor) * quantity
            ).quantize(self._sig_fig)
            description = package.get("description", "")

            if package.get("is_pharma", False):
                if package.get("package_account_id", ""):
                    description = f"{package.get('package_type_name', '')} {package['package_account_id']} {description[:20]}"
                else:
                    description = (
                        f"{package.get('package_type_name', '')} {description}"
                    )

                if package.get("is_time_sensitive", False):
                    description += " 48H Time Sensitive"

                if package.get("is_cos", False):
                    description += " COS"
            elif package.get("package_account_id", ""):
                description = f"{package['package_account_id']} - {description}"

            pack = {
                "Quantity": quantity,
                "Description": description[:100],
                "Height": height_quantity,
                "Length": length,
                "Width": width,
                "Weight": str(weight_quantity),
                "IsDangerousGood": is_dangerous,
                "IsCooler": package.get("is_cooler", False),
                "IsFrozen": package.get("is_frozen", False),
                "IsENV": is_envelope,
                "NogId": package.get("nog_id", "88"),
            }

            if is_dangerous:
                pack["UNNumber"] = un_number

            self._processed_packages.append(pack)

            self._total_packages += int(quantity)
            self._total_weight += weight_quantity
            self._total_dim += dim_weight
