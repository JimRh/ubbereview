"""
    Title: BBE Rate Api
    Description: This file will contain functions related to BBE rate Api.
    Created: July 13, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.carriers.bbe.endpoints.bbe_api_v1 import BBEAPI
from api.apis.services.taxes.taxes import Taxes
from api.exceptions.project import RateException, RequestError
from api.models import API
from api.utilities.date_utility import DateUtility


class BBERate(BBEAPI):
    """
    Class will handle all details about a BBE rate requests.
    """

    def __init__(self, ubbe_request: dict):
        super().__init__(ubbe_request=ubbe_request)
        self._response = []

    def _bbe_quote(self) -> list:
        """
        BBE Quote: Always returns, if not rate sheet is found.
        :return: Quote Dictionary
        """
        return [
            {
                "carrier_id": 1,
                "carrier_name": "BBE",
                "service_code": "BBEQUO",
                "service_name": "Quote",
                "freight": self._zero,
                "surcharge": self._zero,
                "tax": self._zero,
                "tax_percent": self._zero,
                "total": self._zero,
                "transit_days": -1,
            }
        ]

    def _process_cost(self) -> None:
        """
        Get BBE rates for a given lane.
        :return: None
        """
        surcharges = self._zero
        sheet = self.get_rate_sheet_rate()

        if not sheet:
            return None

        if sheet.is_metric:
            weight = self._ubbe_request["total_weight"]
        else:
            weight = self._ubbe_request["total_weight_imperial"]

        # Get freight Cost
        try:
            freight_cost = self._get_freight_cost(sheet, weight).quantize(self._sig_fig)
        except RateException:
            return None

        # Get Fuel Surcharge Cost
        fuel_surcharge = self._get_fuel_surcharge_cost(
            final_weight=weight, freight_cost=freight_cost
        )
        surcharges += fuel_surcharge["cost"]

        # Get Taxes
        try:
            taxes = Taxes(self._destination).get_tax_rate(freight_cost + surcharges)
        except RequestError:
            return None

        total = freight_cost + surcharges + taxes
        tax_percent = ((taxes / (total - taxes)) * self._hundred).quantize(
            self._sig_fig
        )

        estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
            transit=sheet.transit_days,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        self._response.append(
            {
                "carrier_id": sheet.carrier.code,
                "carrier_name": sheet.carrier.name,
                "service_code": sheet.service_code,
                "service_name": sheet.service_name,
                "freight": freight_cost.quantize(self._sig_fig),
                "surcharge": surcharges.quantize(self._sig_fig),
                "tax": taxes,
                "tax_percent": tax_percent.quantize(self._sig_fig),
                "total": total.quantize(self._sig_fig),
                "transit_days": transit,
                "delivery_date": estimated_delivery_date,
            }
        )

    def rate(self, is_quote: bool = False) -> list:
        """
        Gets rate for BBE
        :return: List of BBE Rates
        """

        if is_quote:
            connection.close()
            return self._bbe_quote()

        self._process_cost()

        if not self._response:
            connection.close()
            return []

        connection.close()
        return self._response
