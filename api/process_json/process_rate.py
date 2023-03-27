import copy
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from api.exceptions.project import ViewException
from api.general.convert import Convert
from api.globals.carriers import FEDEX, PUROLATOR, CAN_NORTH, CAN_POST, WESTJET, PUROLATOR_FREIGHT, SEALIFT_CARRIERS, \
    FTL_CARRIERS, COURIERS_CARRIERS, LTL_CARRIERS, AIR_CARRIERS, BUFFALO_AIRWAYS
from api.models import DangerousGood, Carrier, PackageType, SubAccount, CarrierOption
from api.process_json.process_json import ProcessJson


class ProcessRateJson(ProcessJson):

    def __init__(self, gobox_request: dict, user: User, sub_account: SubAccount):
        super(ProcessRateJson, self).__init__(gobox_request, user, sub_account)
        self._carriers = copy.deepcopy(self._gobox_request.get("carrier_id", []))
        self._package_carriers = []
        self._remove_carriers = set()

    def _check_air_cutoff(self, dg: DangerousGood):
        limited_cutoff = dg.air_quantity_cutoff.filter(type="L", cutoff_value=0).exists()
        passenger_cutoff = dg.air_quantity_cutoff.filter(type="P", cutoff_value=0).exists()
        cargo_cutoff = dg.air_quantity_cutoff.filter(type="C", cutoff_value=0).exists()

        if limited_cutoff and passenger_cutoff and cargo_cutoff:
            self._remove_carriers.update([CAN_NORTH, WESTJET])

    # Override
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

    def _check_carrier_flags(self):
        if not self._gobox_request["is_air"]:
            self._remove_carriers.update(AIR_CARRIERS)

        if not self._gobox_request["is_courier"]:
            self._remove_carriers.update(COURIERS_CARRIERS)

        if not self._gobox_request["is_ltl"]:
            self._remove_carriers.update(LTL_CARRIERS)

        if not self._gobox_request["is_ftl"]:
            self._remove_carriers.update(FTL_CARRIERS)

        if not self._gobox_request["is_sealift"]:
            self._remove_carriers.update(SEALIFT_CARRIERS)

    def _check_addresses(self):
        self._gobox_request["origin"]["address"] = self._clean_address(self._gobox_request["origin"]["address"])
        self._gobox_request["destination"]["address"] = self._clean_address(self._gobox_request["destination"]["address"])
        self._gobox_request["origin"]["city"] = self._clean_city(self._gobox_request["origin"]["city"])
        self._gobox_request["destination"]["city"] = self._clean_city(self._gobox_request["destination"]["city"])

        origin = self._gobox_request["origin"]
        destination = self._gobox_request["destination"]

        is_o_kuujjuaq = origin["postal_code"].replace(" ", "").upper() == self._kuujjuaq
        is_d_kuujjuaq = destination["postal_code"].replace(" ", "").upper() == self._kuujjuaq

        if origin["country"] != destination["country"]:
            self._is_international = True
        else:
            is_origin_north = origin["province"] not in self._north
            is_destination_north = destination["province"] not in self._north

            # Remove Canadian North with both province are in the south
            if is_origin_north and is_destination_north and not is_o_kuujjuaq and not is_d_kuujjuaq:
                self._remove_carriers.add(CAN_NORTH)

    def _clean_carriers(self):
        processed_carriers = []

        if self._carriers:
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
        else:
            if self._is_dangerous_good:
                processed_carriers = self._user.groups_user.carrier.filter(is_dangerous_good=True).exclude(
                    code__in=self._remove_carriers
                ).values_list("code", flat=True)
            else:
                processed_carriers = self._user.groups_user.carrier.all().exclude(
                    code__in=self._remove_carriers
                ).values_list("code", flat=True)

        self._gobox_request["carrier_id"] = list(processed_carriers)

    # Override
    def _clean_packages(self):
        total_weight = Decimal("0.00")
        total_volume = Decimal("0.00")
        total_quantity = Decimal("0.0")

        for package in self._gobox_request["packages"]:
            self._convert_package(package=package)

            try:
                package_types = PackageType.objects.get(
                    code=package["package_type"], account__user__username=self._sub_account.client_account.user.username
                )
            except ObjectDoesNotExist:
                errors = [{"package_type": package["package_type"]}]
                raise ViewException(code="501", message="Package Type not found for account.", errors=errors)

            self._package_carriers.append(set(package_types.carrier.values_list("code", flat=True)))

            if package_types.is_pharma:
                self._gobox_request["is_pharma"] = package_types.is_pharma

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

        self._gobox_request["total_quantity"] = total_quantity
        self._gobox_request["total_weight"] = total_weight
        self._gobox_request["total_volume"] = total_volume
        self._gobox_request["total_weight_imperial"] = Convert().kgs_to_lbs(total_weight)
        self._gobox_request["total_volume_imperial"] = Convert().cubic_cms_to_cubic_feet(total_volume)

    def _clean_total_weight(self):

        if self._gobox_request["total_weight_imperial"] >= self._ten_thousand:
            self._remove_carriers.add(PUROLATOR_FREIGHT)

        if self._gobox_request["total_weight"] >= self._ten_thousand:
            self._remove_carriers.update([CAN_NORTH, WESTJET])

    def _clean_carrier_options(self):
        """
            Remove Carriers that do not contain the options passed in.
        """

        for option in self._gobox_request.get("carrier_options", []):
            for carrier in self._carriers:

                if carrier in [BUFFALO_AIRWAYS, CAN_NORTH]:
                    continue

                if not CarrierOption.objects.filter(carrier__code=carrier, option__id=option).exists():
                    self._remove_carriers.add(carrier)

    # Override
    def clean(self):
        self._check_carrier_flags()
        self._clean_packages()
        self._clean_total_weight()
        self._check_addresses()
        self._clean_carrier_options()
        self._clean_carriers()
        self._gobox_request["is_dangerous_goods"] = self._is_dangerous_good
        self._gobox_request["is_international"] = self._is_international
