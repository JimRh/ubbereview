"""
    Title: Manitoulin api
    Description: This file will contain all functions to get Manitoulin common functionality between the endpoints.
    Created: December 19, 2022
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import copy
import json
from decimal import Decimal
from typing import Union

import requests
from django.core.cache import cache
from django.db import connection

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.carriers import MANITOULIN
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, ONE_HOUR_CACHE_TTL


class ManitoulinBaseApi:
    """
    Manitoulin Api Class
    """

    _carrier_name = "Manitoulin"
    _carrier_currency = "CAD"
    _time_critical_service_codes = ["A", "P"]
    _default_transit = 10
    _five_minutes = 60 * 10

    _hundred = Decimal("100.00")
    _sig_fig = Decimal("0.01")
    _sig_fig_weight = Decimal("0")
    _zero = Decimal("0.0")

    _cache_expiry = TWENTY_FOUR_HOURS_CACHE_TTL * 6

    # ubbe option codes
    _delivery_appointment = 1
    _pickup_appointment = 2
    _tailgate = 3
    _heated_truck = 6
    _refrigerated_truck = 5
    _power_tailgate_pickup = 3
    _power_tailgate_delivery = 17
    _inside_pickup = 9
    _inside_delivery = 10

    # Manitoulin Values
    _std_service = "STD"
    _rock_solid_afternoon_service = "A"
    _rock_solid_evening_service = "P"
    _payment_terms = "PPD"
    _business_role = "Third Party"

    # Manitoulin Services
    _services = {
        "LTL": "Standard LTL",
        "ROCKA": "Rock Solid Guarantee By Noon",
        "ROCKP": "Rock Solid Guarantee By 4PM",
    }

    _ship_service_codes = {
        "LTL": "N",
        "ROCKA": "A",
        "ROCKP": "P",
    }

    # Manitoulin class to ubbe Relation
    _freight_class_map = {
        "50.00": "50",
        "55.00": "55",
        "60.00": "60",
        "65.00": "65",
        "70.00": "70",
        "77.50": "77.5",
        "85.00": "85",
        "92.50": "92.5",
        "100.00": "100",
        "110.00": "110",
        "125.00": "125",
        "150.00": "150",
        "175.00": "175",
        "200.00": "200",
        "250.00": "250",
        "300.00": "300",
        "400.00": "400",
        "500.00": "500",
    }

    _pickup_package_type_map = {
        "BAG": "BAGS",
        "BOX": "BOXES",
        "BUNDLES": "BUNDLES",
        "CRATE": "CRATES",
        "DRUM": "DRUMS",
        "ENVELOPE": "ENVELOPES",
        "PAIL": "PAILS",
        "REEL": "REELS",
        "ROLL": "ROLLS",
        "SKID": "SKIDS",
        "TOTES": "TOTES",
        "TUBE": "TUBES",
        "VEHICLE": "VEHICLES",
    }

    _quote_package_type_map = {
        "BAG": "BG",
        "BOX": "BX",
        "BUNDLES": "BD",
        "CRATE": "CR",
        "DRUM": "DR",
        "ENVELOPE": "EN",
        "PAIL": "PL",
        "REEL": "RE",
        "ROLL": "RL",
        "SKID": "SK",
        "TOTES": "TB",
        "TUBE": "TU",
        "VEHICLE": "VH",
    }

    # Manitoulin Urls
    _rate_url = "https://www.mtdirect.ca/api/online_quoting/quote"
    _pickup_url = "https://www.mtdirect.ca/api/online_pickup/submit"
    _ship_url = "https://www.mtdirect.ca/api/bol/save_bol"
    _transit_time_calculator_url = (
        "https://www.mtdirect.ca/api/shippingtools/transit_time_calculator"
    )
    _track = "https://www.mtdirect.ca/api/probill/search/"
    _token_url = "https://www.mtdirect.ca/api/users/auth"
    _bol_pdf = "https://www.mtdirect.ca/api/bol/get_pdf"
    _bol_labels = "https://www.mtdirect.ca/api/bol/get_labels"

    _images_links = "https://www.mtdirect.ca/api/probill/images/links"
    _images_downloads = "https://www.mtdirect.ca/api/probill/images/download"

    def __init__(self, ubbe_request: dict, is_track: bool = False):
        if not is_track:
            self._ubbe_request = copy.deepcopy(ubbe_request)
            self._sub_account = self._ubbe_request["objects"]["sub_account"]
            self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                MANITOULIN
            ]["account"]
            self._carrier = self._ubbe_request["objects"]["carrier_accounts"][
                MANITOULIN
            ]["carrier"]

            self._account_number = self._carrier_account.account_number.decrypt()
            self._username = self._carrier_account.username.decrypt()
            self._password = self._carrier_account.password.decrypt()

            if "dg_service" in self._ubbe_request:
                self._dg_service = self._ubbe_request.pop("dg_service")
            else:
                self._dg_service = None

    def _get_auth(self) -> dict:
        """
        Get auth for manitoulin api call.
        return: auth token
        """

        return {
            "Authorization": f"Token {self.get_token()}",
            "Content-Type": "application/json",
        }

    def _get(self, url: str, params: dict = None) -> Union[list, dict]:
        """
        Make Manitoulin get api call.
        params: url, params
        return: returns either a list or a dictionary as a response
        """

        if not params:
            params = {}

        try:
            response = requests.get(
                url=url,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                headers=self._get_auth(),
                params=params,
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": url, "error": str(e)}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": url})

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_critical.delay(
                location="yrc_base.py line: 116", message=f"{response.text}"
            )
            connection.close()
            raise RequestError(
                response, {"url": url, "error": str(e), "data": params}
            ) from e

        return response

    def _post(self, url: str, request: dict):
        """
        Make Manitoulin post api call.
        params: url, request
        return: returns either a list or a dictionary as a response
        """

        try:
            response = requests.post(
                url=url,
                json=request,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                headers=self._get_auth(),
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(
                None, {"url": url, "error": str(e), "data": request}
            ) from e

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_critical.delay(
                location="yrc_base.py line: 116", message=f"{response.text}"
            )
            connection.close()
            raise RequestError(
                response, {"url": url, "error": str(e), "data": request}
            ) from e

        connection.close()
        return response

    def _get_content(self, url: str, params: dict = None) -> bytes:
        """
        Make Manitoulin get api call to download documents.
        params: url, params
        return: returns a response in bytes
        """

        headers = self._get_auth()
        headers["Content-Type"] = "application/pdf"

        if not params:
            params = {}

        try:
            response = requests.get(
                url=url,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                headers=headers,
                params=params,
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": url, "error": str(e)}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": url})

        return json.loads(response.content)

    def get_token(self):
        """
        Get auth token to make requests
        params: none
        return: returns authentication token as a string
        """
        lookup = f"{str(self._sub_account.subaccount_number)}_manitoulin_token"

        token = cache.get(lookup)

        if not token:
            request = {
                "username": self._username,
                "password": self._password,
                "company": "MANITOULIN",
            }

            try:
                response = requests.post(
                    url=self._token_url, data=request, timeout=DEFAULT_TIMEOUT_SECONDS
                )
            except requests.RequestException as e:
                connection.close()
                raise RequestError(
                    None, {"url": self._token_url, "error": str(e), "data": request}
                ) from e

            try:
                response = response.json()
            except ValueError as e:
                CeleryLogger().l_critical.delay(
                    location="yrc_base.py line: 116", message=f"{response.text}"
                )
                connection.close()
                raise RequestError(
                    response, {"url": self._rate_url, "error": str(e), "data": request}
                ) from e

            token = response["token"]
            cache.set(lookup, token, ONE_HOUR_CACHE_TTL - self._five_minutes)

        return token
