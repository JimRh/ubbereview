import copy
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from api.exceptions.project import ViewException
from api.general.convert import Convert
from api.globals.carriers import FEDEX, PUROLATOR, CAN_POST, SEALIFT_CARRIERS, UBBE_INTERLINE
from api.globals.project import getkey
from api.models import DangerousGood, SealiftSailingDates, PackageType, SubAccount
from api.process_json.process_json import ProcessJson


class ProcessShipJson(ProcessJson):

    # TODO CLEAN UP

    def __init__(self, gobox_request: dict, user: User, sub_account: SubAccount):
        super(ProcessShipJson, self).__init__(gobox_request, user, sub_account)
        self._service = copy.deepcopy(self._gobox_request["service"])
        self._m_carrier = self._service["carrier_id"]
        self._m_service = self._service["service_code"]

        if self._m_carrier == UBBE_INTERLINE:
            self._setup_carriers()

        self._p_carrier = getkey(self._service, 'pickup.carrier_id', None)
        self._d_carrier = getkey(self._service, 'delivery.carrier_id', None)

        self._allowed_carriers = set()
        self._remove_carriers = set()

    def _check_carriers(self, carrier: int, overall_dims, weight: Decimal):

        if carrier in [FEDEX, PUROLATOR]:
            if weight > self._two_ship_max_weight or overall_dims > self._two_ship_overall_dimensions:
                msg = "Carrier: {}, can not ship packages, Dims cannot exceed: {}. Weight cannot exceed: {}".format(
                    carrier,
                    self._two_ship_overall_dimensions,
                    self._two_ship_max_weight
                )

                raise ViewException({"api.error.packages": msg})
        elif carrier == CAN_POST:
            if weight > self._canada_post_max_weight or overall_dims > self._canada_post_overall_dimensions:
                msg = "Carrier: {}, can not ship packages, Dims cannot exceed: {}. Weight cannot exceed: {}".format(
                    carrier,
                    self._canada_post_overall_dimensions,
                    self._canada_post_max_weight
                )

                raise ViewException({"API.Error.Packages": msg})

    # Override
    def _check_dg_package(self, package: dict):
        un_number = package["un_number"]
        packing_group = package["packing_group"]
        proper_shipping_name = package["proper_shipping_name"]

        try:
            dg = DangerousGood.objects.select_related(
                "packing_group",
                "classification__label",
                "specialty_label",
                "excepted_quantity",
                "classification"
            ).prefetch_related(
                "air_quantity_cutoff__packing_instruction__packaging_types",
                "subrisks"
            ).get(
                un_number=un_number,
                packing_group__packing_group=packing_group,
                short_proper_shipping_name=package["proper_shipping_name"]
            )
        except ObjectDoesNotExist:
            raise ViewException({
                "api.error.dangerous_goods": "UN{} in packing group {} with proper shipping name {} does not exist".format(
                        un_number,
                        packing_group,
                        proper_shipping_name
                    )
                }
            )

        package["packing_group_name"] = dg.packing_group.packing_group_str + ": " + dg.packing_group.description
        package["packing_group_str"] = dg.packing_group.packing_group_str
        package["dg_object"] = dg
        package["is_dangerous_good"] = True
        package["class_div"] = dg.classification.verbose_classification()
        package["class"] = dg.classification.classification
        package["division"] = dg.classification.division
        package["subrisks"] = list(dg.subrisks.all())
        package["subrisks_str"] = dg.subrisks_str()
        package["placard_img"] = dg.classification.label
        package["specialty_label"] = dg.specialty_label
        package["is_gross"] = dg.is_gross_measure
        package["dg_state"] = dg.state

        if dg.unit_measure == "K":
            package["measure_unit"] = "KG"
        else:
            package["measure_unit"] = "L"

        package["is_limited"] = False

        self._is_dangerous_good = True

    # Override
    def _clean_packages(self):
        total_weight = Decimal("0.00")
        total_volume = Decimal("0.00")
        total_pieces = 0

        for package in self._gobox_request["packages"]:
            self._convert_package(package=package)

            quantity = Decimal(package["quantity"])
            length = Decimal(package["length"])
            width = Decimal(package["width"])
            height = Decimal(package["height"])
            weight = Decimal(package["weight"])
            overall_dims = length + (2 * width) + (2 * height)

            if self._is_international:
                self._convert_commodities(commodities=package["commodities"])

            try:
                package_type = PackageType.objects.get(
                    code=package["package_type"], account__user__username=self._sub_account.client_account.user.username
                )
            except ObjectDoesNotExist as e:
                raise ViewException({"packages": "Package Type not found for account."})

            package_carriers = list(package_type.carrier.values_list("code", flat=True))

            if package_type.is_pharma:
                self._gobox_request["is_pharma"] = package_type.is_pharma

            if self._m_carrier not in package_carriers:
                raise ViewException({"packages": f"Package Type: {package_type.name}  not allowed for {self._m_carrier}."})

            self._check_carriers(carrier=self._m_carrier, overall_dims=overall_dims, weight=weight)

            if self._p_carrier:

                if self._p_carrier not in package_carriers:
                    raise ViewException({"packages": f"Package Type: {package_type.name} not allowed for {self._p_carrier}."})

                self._check_carriers(carrier=self._p_carrier, overall_dims=overall_dims, weight=weight)

            if self._d_carrier:

                if self._d_carrier not in package_carriers:
                    raise ViewException({"packages": f"Package Type: {package_type.name}  not allowed for {self._d_carrier}."})

                self._check_carriers(carrier=self._d_carrier, overall_dims=overall_dims, weight=weight)

            if package["is_dangerous_good"]:
                self._check_dg_package(package=package)

            volume = (length * width * height * quantity).quantize(self._sig_fig)
            total_pieces += quantity
            total_volume += volume
            total_weight += (weight * quantity).quantize(self._sig_fig)
            package["volume"] = volume / self._cubic_meter_contsant
            package["package_type_name"] = package_type.name

        self._gobox_request["packages"][-1]["is_last"] = True
        self._gobox_request["total_quantity"] = total_pieces
        self._gobox_request["total_pieces"] = total_pieces
        self._gobox_request["total_weight"] = total_weight
        self._gobox_request["total_volume"] = total_volume
        self._gobox_request["total_weight_imperial"] = Convert().kgs_to_lbs(total_weight)
        self._gobox_request["total_volume_imperial"] = Convert().cubic_cms_to_cubic_feet(total_volume)

    def _check_sailing(self):
        sailing = self._m_service[:-3]
        port = self._m_service[2:]

        try:
            sailing = SealiftSailingDates.objects.select_related(
                "port"
            ).get(
                name=sailing,
                port__code=port
            )
        except ObjectDoesNotExist as e:
            raise ViewException({"api.sailing_date.error": "Sailing Date does not exist."})

        self._gobox_request["sailing"] = sailing

    def _setup_carriers(self):
        """
            Setup Interline carriers in pickup and delivery.
        """

        services = self._m_service.split("|")

        self._gobox_request["service"]["pickup"] = {
            "carrier_id": int(services[0]),
            "service_code": services[1]
        }

        self._gobox_request["service"]["delivery"] = {
            "carrier_id": int(services[2]),
            "service_code": services[3]
        }

    # Override
    def clean(self):

        if self._gobox_request["origin"]["country"] != self._gobox_request["destination"]["country"]:
            self._is_international = True

        self._clean_packages()

        if self._m_carrier in SEALIFT_CARRIERS:
            self._check_sailing()

        self._gobox_request["is_international"] = self._is_international
        self._gobox_request["is_dangerous_goods"] = self._is_dangerous_good
