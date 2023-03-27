"""
    Title: RateSheet Base Class
    Description: This file will contain common functions between Rate and Ship.
    Created: February 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
import datetime
from decimal import Decimal

import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import QuerySet
from django.utils import timezone

from api.apis.exchange_rate.exchange_rate import ExchangeRateUtility
from api.apis.services.carrier_options.carrier_options import CarrierOptions
from api.apis.services.carrier_options.mandatory import Mandatory
from api.exceptions.project import ViewException, RateException
from api.exceptions.services import CarrierOptionException
from api.globals.carriers import NEAS, NSSI, MTS
from api.models import RateSheet, FuelSurcharge, CityNameAlias, City


class RateSheetAPI:
    _hundred = Decimal("100.00")
    _thousand = Decimal("1000.00")
    _cubic = Decimal("2.5")
    _sig_fig = Decimal("0.01")
    _zero = Decimal("0.00")
    _minus_one = -1

    # Sealift Only
    _dg_percentage = Decimal("1.20")
    _40_container = 2
    _closed_create = "CC"
    _open_create = "OC"
    _dg_create = "DC"
    _fragile_create = "FC"
    _strapping_create = "ST"
    _strapping_base = "SB"

    # Rate sheet Types
    _per_hundred_pounds = "PHP"
    _per_pound = "PPO"
    _per_revenue_ton = "PRT"
    _per_quantity = "PQA"
    _flat_rate = "FLR"

    _bbe_account = [
        "5edcc144-4546-423a-9fcd-2be2418e4720",  # BBE LIVE
        "b7d32b99-ce39-4629-bb2f-df9c93b1dcca",  # BBE Beta
        "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",  # BBE Ken Local
        "2c0148a6-69d7-4b22-88ed-231a084d2db9",  # Government of Nunavut
        "4a56e920-2a4c-4243-824c-f5afbad0b4ba",  # Government of Nunavut Returns
    ]

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._error_world_request = copy.deepcopy(self._ubbe_request)
        self._sub_account = self._ubbe_request["objects"]["sub_account"]

        self._process_ubbe_data()
        self._clean_error_copy()

    def _apply_exchange_rate(self, sheet: RateSheet, data: dict, is_ship: bool = False):
        from_exchange_rate = ExchangeRateUtility(
            source_currency=sheet.currency, target_currency="CAD"
        ).get_exchange_rate()

        to_exchange_rate = ExchangeRateUtility(
            source_currency="CAD", target_currency=sheet.currency
        ).get_exchange_rate()

        data.update(
            {
                "freight": (data["freight"] * from_exchange_rate).quantize(
                    self._sig_fig
                ),
                "total": (data["total"] * from_exchange_rate).quantize(self._sig_fig),
                "exchange_rate": {
                    "from_source": from_exchange_rate,
                    "to_source": to_exchange_rate,
                    "from_currency": sheet.currency,
                    "to_currency": "CAD",
                },
            }
        )

        if is_ship:
            data["surcharges_cost"] = (
                data["surcharges_cost"] * from_exchange_rate
            ).quantize(self._sig_fig)
            data["taxes"] = (data["taxes"] * from_exchange_rate).quantize(self._sig_fig)
        else:
            data["surcharge"] = (data["surcharge"] * from_exchange_rate).quantize(
                self._sig_fig
            )
            data["tax"] = (data["tax"] * from_exchange_rate).quantize(self._sig_fig)

    def _process_ubbe_data(self) -> None:
        """s
        Pre set used vars as quick class vars
        """
        self._date = datetime.datetime.now(tz=timezone.utc)

        self._carrier_id = self._ubbe_request["carrier_id"]
        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._packages = self._ubbe_request["packages"]
        self._total_quantity = self._ubbe_request.get("total_quantity", 1)

        # Weight Information
        self._total_mass_metric = self._ubbe_request["total_weight"]
        self._total_volume_metric = self._ubbe_request["total_volume"]

        self._total_mass_imperial = self._ubbe_request["total_weight_imperial"]
        self._total_volume_imperial = self._ubbe_request["total_volume_imperial"]

    def _clean_error_copy(self) -> None:
        """
        Remove any objects for celery and redis
        """

        if "dg_service" in self._error_world_request:
            del self._error_world_request["dg_service"]

        if "objects" in self._error_world_request:
            del self._error_world_request["objects"]

    def _get_city_alias(self, city: str, province: str, country: str) -> str:
        """
        Get dispatch for carrier city terminal, if none exist get the default one.
        :return: city str
        """

        city = CityNameAlias.check_alias(
            alias=city,
            province_code=province,
            country_code=country,
            carrier_id=self._carrier_id,
        )

        return city

    def _is_next_day(self) -> bool:
        """
        Get dispatch for carrier city terminal, if none exist get the default one.
        :return:
        """
        if "pickup" not in self._ubbe_request:
            return False

        pickup = self._ubbe_request["pickup"]

        location_timezone = City().get_timezone(
            name=self._origin["city"],
            province=self._origin["province"],
            country=self._origin["country"],
        )

        tz = pytz.timezone(location_timezone)
        current_time = datetime.datetime.now(tz)

        if pickup["date"] == current_time.strftime("%Y-%m-%d"):
            if pickup["start_time"] > current_time.strftime("%H:%M"):
                return True

        return False

    def _get_carrier_options(
        self, sheet: RateSheet, freight_cost: Decimal, is_metric: bool
    ) -> list:
        """
        Get chosen option cost for carrier ratesheet
        :param is_metric: Is metric units
        :param sheet: ratesheet
        :param freight_cost: Freight Cost
        :return: list of option cost
        """

        if is_metric:
            mass = self._total_mass_metric
            volume = self._total_volume_metric
        else:
            mass = self._total_mass_imperial
            volume = self._total_volume_imperial

        try:
            carrier_options = CarrierOptions().get_calculated_option_costs(
                carrier=sheet.carrier,
                options=self._ubbe_request.get("carrier_options", []),
                actual=mass,
                cubic=volume,
                freight=freight_cost,
                date=self._date,
            )
        except CarrierOptionException:
            return []

        return carrier_options

    def _get_freight_cost(self, sheet: RateSheet, weight: Decimal) -> Decimal:
        """
        Get freight cost for a shipment. Imperial Units
        :param sheet: ratesheet
        :param weight: total weight, Biggest between Volume and Mass: Imperial Units
        :return:
        """

        try:
            lane = sheet.rate_sheet_lane_rate_sheet.get(
                min_value__lte=weight, max_value__gte=weight
            )
        except ObjectDoesNotExist:
            raise ViewException(
                {
                    "api.error.rate_sheets": "No lanes for rate sheet {} with weight {}".format(
                        str(sheet), weight
                    )
                }
            )
        except MultipleObjectsReturned:
            raise ViewException(
                {
                    "api.error.rate_sheets": f"Multi Objects {str(sheet)} with weight {weight}"
                }
            )

        if sheet.rs_type == self._flat_rate:
            return Decimal(lane.cost).quantize(self._sig_fig)

        if sheet.rs_type == self._per_pound:
            cost = lane.cost * weight
        elif sheet.rs_type == self._per_quantity:
            cost = lane.cost * self._total_quantity
        else:
            # Default
            cost = (lane.cost * weight) / self._hundred

        return Decimal(max(sheet.minimum_charge, cost)).quantize(self._sig_fig)

    def _get_container_cost(
        self, sheet: RateSheet, qty: Decimal, is_40: bool = False, is_dg: bool = False
    ):
        """
        Get Sealift cost for a container.
        :param sheet: RateSheet Object
        :param qty: Total Containers
        :param is_40: Is the container 40 foot
        :param is_dg: Is the shipment DG
        :return: Cost
        """

        try:
            lane = sheet.rate_sheet_lane_rate_sheet.get(
                min_value__lte=Decimal("0"), max_value__gte=Decimal("0")
            )
        except ObjectDoesNotExist:
            raise RateException(
                {
                    "api.error.rate_sheets": "No lanes for rate sheet {} with weight {}".format(
                        str(sheet), ""
                    )
                }
            )

        if is_40:
            lane_cost = lane.cost * self._40_container

            if is_dg:
                lane_cost = lane_cost * self._dg_percentage
        else:
            if is_dg:
                lane_cost = lane.cost * self._dg_percentage
            else:
                lane_cost = lane.cost

        return qty * lane_cost

    def _get_rev_ton_cost(
        self, sheet: RateSheet, cubic_meter: Decimal, mass: Decimal, is_dg: bool = False
    ) -> Decimal:
        """
        Get Sealift cost for a rev ton or cubic meter.
        :param sheet: RateSheet Object
        :param cubic_meter: Total Cubic Meters
        :param mass: total Mass
        :param is_dg: Is the shipment DG
        :return: Cost
        """

        cubic_meters = cubic_meter / self._cubic
        rev_tons = mass / self._thousand

        weight = max(cubic_meters, rev_tons)

        try:
            lane = sheet.rate_sheet_lane_rate_sheet.get(
                min_value__lte=weight, max_value__gte=weight
            )
        except ObjectDoesNotExist:
            raise RateException(
                {
                    "api.error.rate_sheets": "No lanes for rate sheet {} with weight {}".format(
                        str(sheet), weight
                    )
                }
            )

        if is_dg:
            cost = weight * lane.cost * self._dg_percentage
            return max((sheet.minimum_charge * self._dg_percentage), cost)
        else:
            cost = weight * lane.cost
            return max(sheet.minimum_charge, cost)

    def _get_fuel_surcharge_cost(
        self, carrier_id: int, final_weight: Decimal, freight_cost: Decimal
    ) -> dict:
        """
        Get Fuel Surcharge percentage for carrier and lane, based on Weight and Freight Cost.
        :param carrier_id: Carrier ID
        :param final_weight: Final total weight
        :param freight_cost: Final Freight Cost
        :return: Fuel Surcharge Cost
        """

        if self._origin["country"] == self._destination["country"]:
            fuel_type = "D"
        else:
            fuel_type = "I"

        try:
            fuel_surcharge = FuelSurcharge.objects.get(
                carrier__code=carrier_id, fuel_type=fuel_type
            )
        except ObjectDoesNotExist:
            return {
                "carrier_id": carrier_id,
                "name": "Fuel Surcharge",
                "cost": self._zero,
                "percentage": self._zero,
            }

        return fuel_surcharge.get_json(weight=final_weight, freight_cost=freight_cost)

    def _get_mandatory_options(
        self, sheet: RateSheet, freight_cost: Decimal, is_metric: bool
    ) -> list:
        """
        Get chosen option cost for carrier ratesheet
        :param sheet: ratesheet
        :param freight_cost: Freight Cost
        :param is_metric: Is metric units
        :return: list of option cost
        """

        if is_metric:
            mass = self._total_mass_metric
            volume = self._total_volume_metric
        else:
            mass = self._total_mass_imperial
            volume = self._total_volume_imperial

        mandatory_request = {
            "carrier_id": sheet.carrier.code,
            "is_dg_shipment": self._ubbe_request.get("is_dangerous_shipment", False),
            "origin": self._origin,
            "destination": self._destination,
            "packages": self._packages,
        }

        try:
            mandatory_options = Mandatory().get_calculated_option_costs(
                carrier=sheet.carrier,
                request=mandatory_request,
                actual=mass,
                cubic=volume,
                freight=freight_cost,
                date=self._date,
            )
        except CarrierOptionException:
            mandatory_options = []

        return mandatory_options

    def _process_package_costs(self, sheets: QuerySet, packages: list):
        freight = Decimal("0.00")
        packing_cost = Decimal("0.00")
        sheet = None

        for package in packages:
            qty = Decimal(package["quantity"])
            length = Decimal(package["length"])
            width = Decimal(package["width"])
            height = Decimal(package["height"])
            weight = Decimal(package["weight"])
            package_type = package["package_type"]
            is_dg = package.get("is_dangerous_good", False)
            packing = package.get("packaging", "NA")

            #  TODO FIX PACKAGE TYPE

            if package_type in ["20CONT", "40CONT", "CONTAINER"]:
                sheet = sheets.filter(service_code="20CONT").first()
                if package_type == "40CONT":
                    freight += self._get_container_cost(
                        sheet=sheet, qty=qty, is_dg=is_dg, is_40=True
                    )
                else:
                    freight += self._get_container_cost(
                        sheet=sheet, qty=qty, is_dg=is_dg
                    )
            else:
                sheet = sheets.filter(service_code="NB").first()
                dims = (
                    (length / self._hundred)
                    * (width / self._hundred)
                    * (height / self._hundred)
                )
                cubic_meters = dims * qty
                mass = weight * qty

                packing_cost += self._calculate_packing_cost(
                    sheet=sheet, packing=packing, cubic_meter=cubic_meters
                )

                cost = self._get_rev_ton_cost(
                    sheet=sheet, cubic_meter=cubic_meters, mass=mass, is_dg=is_dg
                )
                freight += cost

        return freight, packing_cost, sheet

    def _get_rate_sheets_sealift(self, carrier_id: int) -> QuerySet:
        """
        Query the DB for the carrier ratesheets.
        :return: QuerySet of Ratesheets for carrier
        """

        rate_sheets = RateSheet.objects.filter(
            origin_city__iexact=CityNameAlias.check_alias(
                self._origin["city"],
                self._origin["province"],
                self._origin["country"],
                carrier_id,
            ),
            destination_city__iexact=CityNameAlias.check_alias(
                self._destination["city"],
                self._destination["province"],
                self._destination["country"],
                carrier_id,
            ),
            origin_province__country__code=self._origin["country"],
            destination_province__country__code=self._destination["country"],
            origin_province__code=self._origin["province"],
            destination_province__code=self._destination["province"],
            carrier__code=carrier_id,
        )

        return rate_sheets

    #  TODO - Remove Below

    def _neas_packing_cost(self, packing, cubic_meters) -> Decimal:
        _closed_create_cost = Decimal("172.09")
        _open_create_cost = Decimal("164.90")
        _dg_create_cost = Decimal("172.09")
        _fragile_create_cost = Decimal("188.96")
        _strapping_create_cost = Decimal("54.80")
        _strapping_base_cost = Decimal("94.45")

        if packing == self._closed_create:
            cost = (cubic_meters * _closed_create_cost).quantize(self._sig_fig)
            return max(cost, _closed_create_cost)
        elif packing == self._open_create:
            cost = (cubic_meters * _open_create_cost).quantize(self._sig_fig)
            return max(cost, _open_create_cost)
        elif packing == self._dg_create:
            cost = (cubic_meters * _dg_create_cost).quantize(self._sig_fig)
            return max(cost, _dg_create_cost)
        elif packing == self._fragile_create:
            cost = (cubic_meters * _fragile_create_cost).quantize(self._sig_fig)
            return max(cost, _fragile_create_cost)
        elif packing == self._strapping_create:
            cost = (cubic_meters * _strapping_create_cost).quantize(self._sig_fig)
            return max(cost, _strapping_create_cost)
        elif packing == self._strapping_base:
            cost = (cubic_meters * _strapping_base_cost).quantize(self._sig_fig)
            return max(cost, _strapping_base_cost)

        return Decimal("0.00")

    def _nssi_packing_cost(self, packing, cubic_meters) -> Decimal:
        _closed_create_cost = Decimal("172.09")
        _open_create_cost = Decimal("164.90")
        _dg_create_cost = Decimal("172.09")
        _fragile_create_cost = Decimal("188.96")
        _strapping_create_cost = Decimal("54.80")
        _strapping_base_cost = Decimal("94.45")

        if packing == self._closed_create:
            cost = (cubic_meters * _closed_create_cost).quantize(self._sig_fig)
            return max(cost, _closed_create_cost)
        elif packing == self._open_create:
            cost = (cubic_meters * _open_create_cost).quantize(self._sig_fig)
            return max(cost, _open_create_cost)
        elif packing == self._dg_create:
            cost = (cubic_meters * _dg_create_cost).quantize(self._sig_fig)
            return max(cost, _dg_create_cost)
        elif packing == self._fragile_create:
            cost = (cubic_meters * _fragile_create_cost).quantize(self._sig_fig)
            return max(cost, _fragile_create_cost)
        elif packing == self._strapping_create:
            cost = (cubic_meters * _strapping_create_cost).quantize(self._sig_fig)
            return max(cost, _strapping_create_cost)
        elif packing == self._strapping_base:
            cost = (cubic_meters * _strapping_base_cost).quantize(self._sig_fig)
            return max(cost, _strapping_base_cost)

        return Decimal("0.00")

    def _mts_packing_cost(self, packing, cubic_meters) -> Decimal:
        _closed_create_cost = Decimal("172.09")
        _open_create_cost = Decimal("164.90")
        _dg_create_cost = Decimal("172.09")
        _fragile_create_cost = Decimal("188.96")
        _strapping_create_cost = Decimal("54.80")
        _strapping_base_cost = Decimal("94.45")

        if packing == self._closed_create:
            cost = (cubic_meters * _closed_create_cost).quantize(self._sig_fig)
            return max(cost, _closed_create_cost)
        elif packing == self._open_create:
            cost = (cubic_meters * _open_create_cost).quantize(self._sig_fig)
            return max(cost, _open_create_cost)
        elif packing == self._dg_create:
            cost = (cubic_meters * _dg_create_cost).quantize(self._sig_fig)
            return max(cost, _dg_create_cost)
        elif packing == self._fragile_create:
            cost = (cubic_meters * _fragile_create_cost).quantize(self._sig_fig)
            return max(cost, _fragile_create_cost)
        elif packing == self._strapping_create:
            cost = (cubic_meters * _strapping_create_cost).quantize(self._sig_fig)
            return max(cost, _strapping_create_cost)
        elif packing == self._strapping_base:
            cost = (cubic_meters * _strapping_base_cost).quantize(self._sig_fig)
            return max(cost, _strapping_base_cost)

        return Decimal("0.00")

    def _calculate_packing_cost(
        self, sheet: RateSheet, packing: str, cubic_meter: Decimal
    ):
        cubic_meters = cubic_meter / self._cubic

        if sheet.carrier.code == NEAS:
            return self._neas_packing_cost(packing=packing, cubic_meters=cubic_meters)
        elif sheet.carrier.code == NSSI:
            return self._nssi_packing_cost(packing=packing, cubic_meters=cubic_meters)
        elif sheet.carrier.code == MTS:
            return self._mts_packing_cost(packing=packing, cubic_meters=cubic_meters)

        return Decimal("0.00")
