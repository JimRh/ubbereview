"""
    Title: Cargojet Base api
    Description: This file will contain all functions to get Cargojet Common Functionality.
    Created: Sept 27, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal
from typing import Union

import requests
from django.db import connection

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.carriers import CARGO_JET
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from brain.settings import CARGOJET_BASE_URL


class CargojetApi:
    """
    Cargojet Api Class

    Carrier Account:

        Api Key -> Api Key
        Contract Number -> Cus COD
    """

    _carrier_name = "Cargojet"
    _normal_service = "Normal"
    _standby_service = "Standby"
    _two_day_service = "Two Days"
    _url = CARGOJET_BASE_URL

    _transit_time = 1
    _hundred = Decimal("100.00")
    _sig_fig = Decimal("0.01")

    _20_hundred_hours = 20

    # Locations
    _yeg = "YEG"
    _yyc = "YYC"
    _yvr = "YVR"
    _ywg = "YWG"
    _yqm = "YQM"
    _yyt = "YYT"
    _yhz = "YHZ"
    _ymx = "YMX"
    _yow = "YOW"
    _yhm = "YHM"
    _yyz = "YYZ"
    _yqr = "YQR"
    _yxe = "YXE"

    # Package Type
    _commodity_gen = "GEN"
    _commodity_food = "FOOD"
    _commodity_cooler_food = "COL"
    _commodity_frozen_food = "FRO"
    _commodity_drug = "DRUG"
    _commodity_dg = "DG"
    _commodity_mail = "MAIL"

    def __init__(self, ubbe_request: dict, is_track: bool = False):
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._auth = {}

        if not is_track:
            self._sub_account = self._ubbe_request["objects"]["sub_account"]
            self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                CARGO_JET
            ]["account"]
            self._carrier = self._ubbe_request["objects"]["carrier_accounts"][
                CARGO_JET
            ]["carrier"]

            self._api_key = self._carrier_account.api_key.decrypt()
            self._customer_code = self._carrier_account.contract_number.decrypt()
            self._auth = {
                "P_CUSCOD": self._customer_code,
                "P_KEY": self._api_key,
                "User-Agent": "ubbe/1.40.0",
            }

            if "dg_service" in self._ubbe_request:
                self._dg_service = self._ubbe_request.pop("dg_service")
            else:
                self._dg_service = None

    def _get(
        self, url: str, params: dict = None, headers: dict = None
    ) -> Union[list, dict]:
        """
        Make Cargojet get api call.
        """

        if not params:
            params = {}

        if not headers:
            headers = {}

        headers.update(self._auth)

        try:
            response = requests.get(
                url=url, timeout=DEFAULT_TIMEOUT_SECONDS, headers=headers, params=params
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
            connection.close()
            raise RequestError(response, {"url": url, "error": str(e)}) from e

        connection.close()
        return response

    def _post(self, url: str, data: dict) -> Union[list, dict, Decimal]:
        """
        Make Cargojet post api call.
        """

        try:
            response = requests.post(
                url=url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS, headers=self._auth
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": url, "error": str(e), "data": data}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": url, "data": data})

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_critical.delay(
                location="cargojet_api.py line: 52", message=f"{response.text}"
            )
            connection.close()
            raise RequestError(
                response, {"url": url, "error": str(e), "data": data}
            ) from e

        connection.close()
        return response
