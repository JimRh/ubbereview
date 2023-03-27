"""
    Title: Action Express Base api
    Description: This file will contain all functions to get Action Express Common Functionality.
    Created: June 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal
from typing import Union

import requests
from django.db import connection

from api.exceptions.project import RequestError
from api.globals.carriers import ACTION_EXPRESS
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from brain.settings import ACTION_EXPRESS_BASE_URL


class ActionExpressApi:
    """
    Purolator Api Class

    Carrier Account:

        Api Key -> Api Key
        Account Number -> Price Set
        Contract Number -> Customer ID

    """

    _carrier_name = "Action Express"
    _url = ACTION_EXPRESS_BASE_URL

    _BOL = "BOL"
    _LABEL = "SL"
    _WAYBILL = "WB"
    _document_types = [_LABEL, _WAYBILL]

    _transit_time = 1
    _same_day = 0

    _sig_fig = Decimal("0.01")

    def __init__(self, ubbe_request: dict, is_track: bool = False):
        self._ubbe_request = copy.deepcopy(ubbe_request)

        if not is_track:
            self._sub_account = self._ubbe_request["objects"]["sub_account"]
            self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                ACTION_EXPRESS
            ]["account"]
            self._carrier = self._ubbe_request["objects"]["carrier_accounts"][
                ACTION_EXPRESS
            ]["carrier"]

            self._auth = {"Authorization": self._carrier_account.api_key.decrypt()}
            self._price_set = self._carrier_account.account_number.decrypt()
            self._customer_id = self._carrier_account.contract_number.decrypt()

    def _get(
        self, url: str, params: dict = None, headers: dict = None
    ) -> Union[list, dict]:
        """
        Make Action Express api call.
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
        Make Action Express api call.
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
            connection.close()
            raise RequestError(
                response, {"url": url, "error": str(e), "data": data}
            ) from e

        connection.close()
        return response
