"""

"""
import copy
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist

from api.exceptions.project import ViewException
from api.general.convert import Convert
from api.globals.carriers import AIR_CARRIERS, COURIERS_CARRIERS, LTL_CARRIERS, FTL_CARRIERS, SEALIFT_CARRIERS, \
    CAN_NORTH, CAN_POST, FEDEX, PUROLATOR, WESTJET, PUROLATOR_FREIGHT, BUFFALO_AIRWAYS
from api.models import SubAccount, PackageType, DangerousGood, Carrier, CarrierOption
from api.parse_requests.parse_request import ParseRequest


class ParseRateRequest(ParseRequest):
    """
        Parse Rate Request
    """

    def __init__(self, ubbe_request: dict, sub_account: SubAccount):
        super(ParseRateRequest, self).__init__(ubbe_request, sub_account)

        self._carriers = set(copy.deepcopy(self._ubbe_request.get("carrier_id", [])))
        self._remove_carriers = set()
        self._package_carriers = []

    def _check_air_cutoff(self, dg: DangerousGood):
        limited_cutoff = dg.air_quantity_cutoff.filter(type="L", cutoff_value=0).exists()
        passenger_cutoff = dg.air_quantity_cutoff.filter(type="P", cutoff_value=0).exists()
        cargo_cutoff = dg.air_quantity_cutoff.filter(type="C", cutoff_value=0).exists()

        if limited_cutoff and passenger_cutoff and cargo_cutoff:
            self._remove_carriers.update([CAN_NORTH, WESTJET])

    def _check_carriers(self, length: Decimal, width: Decimal, height: Decimal, weight: Decimal):
        """
            Check package dimensions and weight and remove any carriers that are over their limits.
            :param length: Package Length
            :param width: Package Width
            :param height: Package Height
            :param weight: Package Weight
            :return:
        """
        result = length + (2 * width) + (2 * height)

        if weight > self._two_ship_max_weight or result > self._two_ship_overall_dimensions:
            self._remove_carriers.update([PUROLATOR, FEDEX])

        if weight > self._canada_post_max_weight or result > self._canada_post_overall_dimensions:
            self._remove_carriers.add(CAN_POST)

    def _check_dg_package(self, package: dict):
        un_number = package["un_number"]
        packing_group = package["packing_group"]
        proper_shipping_name = package["proper_shipping_name"]

        try:
            dg = DangerousGood.objects.prefetch_related(
                "air_quantity_cutoff"
            ).get(
                un_number=un_number,
                packing_group__packing_group=packing_group,
                short_proper_shipping_name=proper_shipping_name
            )
        except ObjectDoesNotExist:
            errors = [
                {"un_number": un_number, "packing_group": packing_group, "proper_shipping_name": proper_shipping_name}
            ]
            message = f"UN{un_number} in packing group {packing_group} with name {proper_shipping_name} does not exist"
            raise ViewException(code="500", message=message, errors=errors)

        if un_number not in self._battery_un_numbers:
            self._remove_carriers.update([CAN_POST])

        self._check_air_cutoff(dg=dg)

        package["is_dangerous_good"] = True
        self._is_dangerous_good = True

    def _parse_address(self):
        """
            Remove carriers based on the address information.
            :return:
        """
        remove_carriers = set()

        self._ubbe_request["origin"]["address"] = self._clean_address(self._ubbe_request["origin"]["address"])
        self._ubbe_request["destination"]["address"] = self._clean_address(self._ubbe_request["destination"]["address"])
        self._ubbe_request["origin"]["city"] = self._clean_city(self._ubbe_request["origin"]["city"])
        self._ubbe_request["destination"]["city"] = self._clean_city(self._ubbe_request["destination"]["city"])

        origin = self._ubbe_request["origin"]
        destination = self._ubbe_request["destination"]

        is_o_kuujjuaq = origin["postal_code"].replace(" ", "").upper() == self._kuujjuaq
        is_d_kuujjuaq = destination["postal_code"].replace(" ", "").upper() == self._kuujjuaq

        if origin["country"] != destination["country"]:
            self._is_international = True
        else:
            is_origin_north = origin["province"] not in self._north
            is_destination_north = destination["province"] not in self._north

            # Remove Canadian North with both province are in the south
            if is_origin_north and is_destination_north and not is_o_kuujjuaq and not is_d_kuujjuaq:
                remove_carriers.add(CAN_NORTH)

        self._carriers = self._carriers - remove_carriers

    def _parse_carrier_flags(self):
        """
            Remove carriers based on the rate request carrier flags.
            :return:
        """
        remove_carriers = set()

        if not self._ubbe_request["is_air"]:
            remove_carriers.update(AIR_CARRIERS)

        if not self._ubbe_request["is_courier"]:
            remove_carriers.update(COURIERS_CARRIERS)

        if not self._ubbe_request["is_ltl"]:
            remove_carriers.update(LTL_CARRIERS)

        if not self._ubbe_request["is_ftl"]:
            remove_carriers.update(FTL_CARRIERS)

        if not self._ubbe_request["is_sealift"]:
            remove_carriers.update(SEALIFT_CARRIERS)

        self._carriers = self._carriers - remove_carriers

    def _parse_carrier_options(self):
        """
            Remove Carriers that do not contain the options passed in.
        """
        remove_carriers = set()

        for option in self._ubbe_request.get("carrier_options", []):
            for carrier in self._carriers:

                if carrier in [BUFFALO_AIRWAYS, CAN_NORTH]:
                    continue

                if not CarrierOption.objects.filter(carrier__code=carrier, option__id=option).exists():
                    remove_carriers.add(carrier)

        self._carriers = self._carriers - remove_carriers

    def _parse_packages(self):
        total_weight = Decimal("0.00")
        total_volume = Decimal("0.00")
        total_quantity = Decimal("0.0")

        for package in self._ubbe_request["packages"]:
            self._convert_package(package=package)

            try:
                package_types = PackageType.objects.get(
                    code=package["package_type"],
                    account__user__username=self._sub_account.client_account.user.username
                )
            except ObjectDoesNotExist:
                errors = [{"package_type": package["package_type"]}]
                raise ViewException(code="501", message="Package Type not found for account.", errors=errors)

            self._package_carriers.append(set(package_types.carrier.values_list("code", flat=True)))

            if package_types.is_pharma:
                self._ubbe_request["is_pharma"] = package_types.is_pharma

            quantity = Decimal(package["quantity"])
            length = Decimal(package["length"])
            width = Decimal(package["width"])
            height = Decimal(package["height"])
            weight = Decimal(package["weight"])

            if 'description' not in package:
                package["description"] = "Quoting"

            self._check_carriers(length=length, width=width, height=height, weight=weight)

            if "un_number" in package:
                self._check_dg_package(package=package)

            total_volume += (length * width * height * quantity).quantize(self._sig_fig)
            total_weight += (weight * quantity).quantize(self._sig_fig)
            total_quantity += quantity

        self._ubbe_request["total_quantity"] = total_quantity
        self._ubbe_request["total_weight"] = total_weight
        self._ubbe_request["total_volume"] = total_volume
        self._ubbe_request["total_weight_imperial"] = Convert().kgs_to_lbs(total_weight)
        self._ubbe_request["total_volume_imperial"] = Convert().cubic_cms_to_cubic_feet(total_volume)

    def _parse_total_weight(self):

        if self._ubbe_request["total_weight_imperial"] >= self._ten_thousand:
            self._remove_carriers.add(PUROLATOR_FREIGHT)

        if self._ubbe_request["total_weight"] >= self._ten_thousand:
            self._remove_carriers.update([CAN_NORTH, WESTJET])

    def _clean_carriers(self):
        """

            :return:
        """
        processed_carriers = []

        carriers = set(self._carriers)

        for package_carriers in self._package_carriers:
            carriers = carriers.intersection(package_carriers)

        for carrier in carriers:

            if carrier in self._remove_carriers:
                continue

            if self._is_dangerous_good:
                try:
                    Carrier.objects.get(code=carrier, is_dangerous_good=True)
                except ObjectDoesNotExist:
                    continue

            processed_carriers.append(carrier)

        self._ubbe_request["carrier_id"] = list(processed_carriers)

    def parse(self):
        """
            Parse Request
        """

        self._parse_carrier_flags()
        self._parse_address()
        self._parse_packages()
        self._parse_total_weight()
        self._parse_carrier_options()
        self._clean_carriers()

        self._ubbe_request["is_dangerous_goods"] = self._is_dangerous_good
        self._ubbe_request["is_international"] = self._is_international
