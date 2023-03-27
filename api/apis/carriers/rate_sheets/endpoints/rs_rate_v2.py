"""
    Title: RateSheet rate
    Description: This file will contain functions related to Rating.
    Created: February 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import connection
from django.utils import timezone

from api.apis.carriers.rate_sheets.endpoints.rs_api_v2 import RateSheetAPI
from api.apis.services.taxes.taxes import Taxes
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException, RequestError, RateException
from api.globals.carriers import FATHOM
from api.models import API, RateSheet, CityNameAlias
from api.utilities.date_utility import DateUtility


class RateSheetRate(RateSheetAPI):
    def __init__(
        self,
        ubbe_request: dict,
        is_courier: bool = True,
        is_ltl: bool = True,
        is_ftl: bool = True,
        is_sealift: bool = False,
        is_air: bool = True,
    ):
        super(RateSheetRate, self).__init__(ubbe_request=ubbe_request)
        self._couriers = []
        self._ltl = []
        self._ftl = []
        self._sealift = []
        self._air = []
        self._is_courier = is_courier
        self._is_ltl = is_ltl
        self._is_ftl = is_ftl
        self._is_sealift = is_sealift
        self._is_air = is_air

    def _formant(
        self,
        sheet: RateSheet,
        freight: Decimal,
        surcharges: Decimal,
        tax: Decimal,
        total: Decimal,
    ) -> dict:
        """
        Format individual RateSheet Rate
        :param sheet: RateSheet Object
        :param freight: Fright Cost
        :param surcharges:  Surcharge Cost
        :param tax: Tax Cost
        :param total: Final Cost
        :return: Formatted rate dict
        """

        if sheet.transit_days > 0:
            if self._is_next_day():
                transit = sheet.transit_days + 1
            else:
                transit = sheet.transit_days

        else:
            transit = sheet.transit_days

        estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
            transit=transit,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        ret = {
            "carrier_id": sheet.carrier.code,
            "carrier_name": sheet.carrier.name,
            "service_code": sheet.service_code,
            "service_name": sheet.service_name,
            "freight": freight,
            "surcharge": surcharges,
            "tax": tax,
            "tax_percent": ((tax / (total - tax)) * self._hundred).quantize(
                self._sig_fig
            ),
            "total": total,
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
        }

        if sheet.carrier.code in self._air:
            ret.update(
                {
                    "mid_o": copy.deepcopy(self._ubbe_request["mid_o"]),
                    "mid_d": copy.deepcopy(self._ubbe_request["mid_d"]),
                }
            )

        if sheet.currency != "CAD":
            self._apply_exchange_rate(sheet=sheet, data=ret)

        return ret

    def _format_sealift(
        self,
        sheet: RateSheet,
        freight: Decimal,
        surcharges: Decimal,
        tax: Decimal,
        total: Decimal,
        service: str,
        service_code: str,
        crate_cost: int,
    ) -> dict:
        """
        Format sealift lane.
        :return: formatted rates
        """
        return {
            "carrier_id": sheet.carrier.code,
            "carrier_name": sheet.carrier.name,
            "service_code": service_code + copy.deepcopy(self._origin["base"]),
            "service_name": service,
            "freight": freight,
            "crate_cost": crate_cost,
            "surcharge": surcharges,
            "tax": tax,
            "tax_percent": ((tax / (total - tax)) * self._hundred).quantize(
                self._sig_fig
            ),
            "total": total,
            "transit_days": sheet.transit_days,
            "mid_o": copy.deepcopy(self._ubbe_request["mid_o"]),
            "mid_d": copy.deepcopy(self._ubbe_request["mid_d"]),
        }

    def _get_rate_sheets(self, carrier_ids: list) -> list:
        """
        Get RateSheets for all carriers in ubbe request.
        :param carrier_ids:
        :return: list of ratesheets
        """

        all_rate_sheets = []

        for code in carrier_ids:
            o_city = CityNameAlias.check_alias(
                alias=self._origin["city"],
                province_code=self._origin["province"],
                country_code=self._origin["country"],
                carrier_id=code,
            )

            d_city = CityNameAlias.check_alias(
                alias=self._destination["city"],
                province_code=self._destination["province"],
                country_code=self._destination["country"],
                carrier_id=code,
            )

            rate_sheets = RateSheet.objects.filter(
                sub_account=self._sub_account,
                origin_city=o_city,
                destination_city=d_city,
                origin_province__country__code=self._origin["country"],
                destination_province__country__code=self._destination["country"],
                origin_province__code=self._origin["province"],
                destination_province__code=self._destination["province"],
                carrier__code=code,
            )

            if not rate_sheets:
                rate_sheets = RateSheet.objects.filter(
                    sub_account__is_default=True,
                    origin_city=o_city,
                    destination_city=d_city,
                    origin_province__country__code=self._origin["country"],
                    destination_province__country__code=self._destination["country"],
                    origin_province__code=self._origin["province"],
                    destination_province__code=self._destination["province"],
                    carrier__code=code,
                )

            all_rate_sheets.extend(rate_sheets)

        return all_rate_sheets

    def _separate_carriers(self) -> None:
        """
        Separate Carrier Modes
        """

        courier_list = self._ubbe_request["objects"]["courier_list"]
        ltl_list = self._ubbe_request["objects"]["ltl_list"]
        ftl_list = self._ubbe_request["objects"]["ftl_list"]
        air_list = self._ubbe_request["objects"]["air_list"]

        for code in self._carrier_id:
            if code in courier_list:
                self._couriers.append(code)
            if code in ltl_list:
                self._ltl.append(code)
            if code in ftl_list:
                self._ftl.append(code)
            if code in air_list:
                self._air.append(code)

    def rate_normal(self, carrier_ids: list) -> list:
        """
        Rate all carriers and format rates for api response
        :param carrier_ids: list of carrier ids
        :return: list of rates
        """

        today = datetime.datetime.now().replace(tzinfo=timezone.utc)
        rates = []
        rate_sheets = self._get_rate_sheets(carrier_ids=carrier_ids)

        if not rate_sheets:
            return []

        total_mass = self._total_mass_imperial
        total_volume = self._total_volume_imperial

        for sheet in rate_sheets:
            if sheet.expiry_date <= today:
                # Skip rate sheet as it as expired
                continue

            surcharges = self._zero
            dimensional_weight = total_volume * sheet.carrier.linear_weight
            final_weight = max(dimensional_weight, total_mass)
            final_weight = Decimal(final_weight).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )

            try:
                freight_cost = self._get_freight_cost(sheet=sheet, weight=final_weight)
            except ViewException as e:
                CeleryLogger().l_critical.delay(
                    location="rate_rate.py line: 211",
                    message="rate_rate: {}".format(e.message),
                )
                continue

            # Get Carrier and Mandatory Options
            surcharges_list = self._get_carrier_options(
                sheet=sheet, freight_cost=freight_cost, is_metric=False
            )
            surcharges_list.extend(
                self._get_mandatory_options(
                    sheet=sheet, freight_cost=freight_cost, is_metric=False
                )
            )

            for option in surcharges_list:
                surcharges += option["cost"]

            # Get Fuel Surcharge
            fuel_surcharge = self._get_fuel_surcharge_cost(
                carrier_id=sheet.carrier.code,
                final_weight=final_weight,
                freight_cost=freight_cost,
            )
            surcharges += fuel_surcharge["cost"]

            try:
                taxes = Taxes(self._destination).get_tax_rate(freight_cost + surcharges)
            except RequestError:
                continue

            total = freight_cost + surcharges + taxes

            rates.append(
                self._formant(
                    sheet=sheet,
                    freight=freight_cost,
                    surcharges=surcharges,
                    tax=taxes,
                    total=total,
                )
            )

        return rates

    def _rate_sealift(self, carrier_id: int) -> list:
        """
        Process the final cost for a sealift lane and format the response
        :param carrier_id: carrier id
        :return: list of rates
        """
        rates = []
        surcharges = Decimal("0.00")

        # Get all Rate Sheets for Carrier for lane
        rate_sheets = self._get_rate_sheets_sealift(carrier_id=carrier_id)

        if not rate_sheets:
            raise RateException("No Rate Sheet.")

        freight_cost, option_cost, sheet = self._process_package_costs(
            sheets=rate_sheets, packages=self._packages
        )
        crate_cost = option_cost
        surcharges += option_cost

        # Get Carrier and Mandatory Options
        surcharges_list = self._get_carrier_options(
            sheet=sheet, freight_cost=freight_cost, is_metric=True
        )
        surcharges_list.extend(
            self._get_mandatory_options(
                sheet=sheet, freight_cost=freight_cost, is_metric=True
            )
        )

        for option in surcharges_list:
            surcharges += option["cost"]

        fuel_surcharge = self._get_fuel_surcharge_cost(
            carrier_id=carrier_id,
            final_weight=self._total_mass_metric,
            freight_cost=freight_cost,
        )
        surcharges += fuel_surcharge["cost"]

        try:
            taxes = Taxes(self._destination).get_tax_rate(freight_cost + surcharges)
        except RequestError as e:
            raise RateException(e)

        total = freight_cost + surcharges + taxes

        for sailing in self._ubbe_request["sailings"]:
            data = sailing.split(":")

            formatted_rate = self._format_sealift(
                sheet=sheet,
                freight=freight_cost,
                surcharges=surcharges,
                tax=taxes,
                total=total,
                service=data[0],
                service_code=data[1],
                crate_cost=crate_cost,
            )

            if sheet.carrier.code == FATHOM:
                formatted_rate["delivery_date"] = "2021-08-01T00:00:00"

            rates.append(formatted_rate)

        return rates

    def rate(self) -> list:
        """
        Get Rates for LTL, FTL, and Courier via RateSheets
        :return: list of rates
        """
        rates = []

        if self._is_sealift:
            if not API.objects.get(name="Sealift").active:
                connection.close()
                return []

            for carrier_id in self._carrier_id:
                try:
                    rates = self._rate_sealift(carrier_id=carrier_id)
                except RateException as e:
                    CeleryLogger().l_info.delay(
                        location="Sealift_rate.py line: 117",
                        message="Sealift_rate: {}".format(e.message),
                    )
                    continue

            connection.close()
            return rates

        self._separate_carriers()

        if self._is_courier:
            rates.extend(self.rate_normal(carrier_ids=self._couriers))

        if self._is_ltl:
            rates.extend(self.rate_normal(carrier_ids=self._ltl))

        if self._is_ftl:
            rates.extend(self.rate_normal(carrier_ids=self._ftl))

        if self._is_air:
            rates.extend(self.rate_normal(carrier_ids=self._air))

        connection.close()
        return rates
