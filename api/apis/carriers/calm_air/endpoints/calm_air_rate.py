"""
    Title: Calm Air Rate Class
    Description: This file will contain functions related to Calm Air Rate Apis.
    Created: August 20, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
import random
from decimal import Decimal

import requests

from django.core.cache import cache
from django.db import connection
from lxml import etree

from api.apis.carriers.calm_air.endpoints.calm_air_base import CalmAirBase
from api.apis.services.taxes.taxes import Taxes
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, RateException
from api.globals.carriers import CALM_AIR
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.utilities.date_utility import DateUtility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CalmAirRate(CalmAirBase):
    """
    Class will handle all details about a Calm Air rate request and return appropriate data.

    Units: Metric Units are used for this api
    """

    _rate_end = "/rates/searchrates"

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._request = None
        self._request_response = None
        self._responses = []
        self._url = self._base_url + self._rate_end

    def _build(self) -> None:
        """
        Build Calm Air rate params.
        """

        self._request = {
            "origin_airport": self._origin["base"],
            "dest_airport": self._destination["base"],
            "currency_code": "CAD",
            "declared_value": Decimal("0"),
            "user_name": self._login,
            "customer_account_number": self._account_number,
            "access_key": self._password,
        }

        packages = self._build_packages()
        self._request.update(packages)

    def _format_response(self) -> None:
        """
        Formant Calm Air rate response into ubbe json response.
        """
        try:
            tax_rate = Taxes(self._destination).get_tax()
        except Exception:
            tax_rate = None

        for rate in self._request_response:
            total = Decimal(str(rate[5].text)).quantize(Decimal(".01"))
            tax = Decimal("0").quantize(Decimal(".01"))
            tax_percent = Decimal("0").quantize(Decimal(".01"))
            freight = Decimal("0").quantize(Decimal(".01"))
            service_code = str(rate[3].text)

            if str(rate[3].text) in self._remove_services:
                continue

            if tax_rate:
                tax_percent = tax_rate.tax_rate
                tax = total - (total / tax_rate.decimal_plus)
                freight = total - tax

            new_code = f'{service_code}-{"{:010d}".format(random.randint(1, 99999))}'

            while cache.get(new_code):
                new_code = (
                    f'{service_code}-{"{:010d}".format(random.randint(1, 99999))}'
                )

            estimated_delivery_date, transit = DateUtility(
                pickup=self._ubbe_request.get("pickup", {})
            ).get_estimated_delivery(
                transit=self._services_transit.get("service_code", 4),
                country=self._ubbe_request["origin"]["country"],
                province=self._ubbe_request["origin"]["province"],
            )

            rate = {
                "carrier_id": CALM_AIR,
                "carrier_name": self._carrier_name,
                "service_code": new_code,
                "service_name": str(rate[4].text).title(),
                "freight": freight,
                "surcharge": Decimal("0").quantize(Decimal(".01")),
                "tax": tax,
                "tax_percent": tax_percent,
                "total": total,
                "transit_days": transit,
                "delivery_date": estimated_delivery_date,
                "mid_o": copy.deepcopy(self._ubbe_request["mid_o"]),
                "mid_d": copy.deepcopy(self._ubbe_request["mid_d"]),
            }

            self._responses.append(rate)
            cache.set(new_code, rate, TWENTY_FOUR_HOURS_CACHE_TTL)

    def _post(self) -> None:
        """
        Make Calm Air rate call
        """

        try:
            response = requests.get(
                self._url, params=self._request, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.RequestException as e:
            connection.close()
            CeleryLogger().l_info.delay(
                location="calm_air_rate.py line: 97",
                message=f"Calm Air Rate posting data: {self._request}",
            )
            raise RequestError(None, self._request) from e

        if not response.ok:
            connection.close()
            CeleryLogger().l_info.delay(
                location="calm_air_rate.py line: 105",
                message=f"Calm Air Rate posting data: {self._request} \nCalm Air return data: {response.text}",
            )
            raise RequestError(response, self._request)

        if "ERRORMESSAGE" not in response.text:
            self._request_response = etree.fromstring(response.content)

    def rate(self):
        """
        Get rates for Calm Air
        :return: list of dictionary rates
        """

        # build requests for Calm Air
        try:
            self._build()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 134",
                message=f"Calm Air Rate: {str(e)}",
            )
            connection.close()
            return []

        # build requests
        try:
            self._post()
        except RequestError as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 145",
                message=f"Calm Air Rate: {str(e)}",
            )
            connection.close()
            return []

        if not self._request_response:
            connection.close()
            return []

        # build requests
        try:
            self._format_response()
        except RequestError as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 156",
                message=f"Calm Air Rate: {str(e)}",
            )
            connection.close()
            return []
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 177",
                message=f"Calm Air Rate: {str(e)}, Data: {str(self._request_response)}",
            )
            connection.close()
            return []

        connection.close()
        return self._responses
