"""
    Title: Exchange Rate Api
    Description: This file will contain functions related to exchange rate api.
    Created: October 5, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

import requests
from django.db import connection

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from brain.settings import OPEN_EXCHANGE_API_KEY


class OpenExchangeRateApi:
    """
        Exchange Rate Interface.
    """
    _url = "https://openexchangerates.org/api/latest.json"

    def __init__(self, source: str, target: str) -> None:
        self._source = source
        self._target = target

    def _get(self):
        """
            Get exchange rate from open exchange rates.
            :return:
        """

        params = {
            "app_id": OPEN_EXCHANGE_API_KEY,
            "base": self._source,
            "symbols": f"{self._target}"
        }

        try:
            response = requests.get(url=self._url, timeout=DEFAULT_TIMEOUT_SECONDS, params=params)
        except requests.RequestException as e:
            connection.close()
            CeleryLogger().l_error.delay(
                location="exchange_rate_api.py line: 359",
                message=f"ExchangeRate: Request Failed. \n{str(e)}"
            )
            raise ViewException(code="9006", message="ExchangeRate: Request Failed", errors=[])

        if not response.ok:
            connection.close()
            CeleryLogger().l_error.delay(
                location="exchange_rate_api.py line: 359",
                message=f"ExchangeRate: Request not ok. \n{str(response.text)}"
            )
            raise ViewException(code="9007", message="ExchangeRate: Request not ok", errors=[])

        try:
            response = response.json()
        except ValueError as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="exchange_rate_api.py line: 359", message=f"ExchangeRate: Failed to load data. \n{str(e)}"
            )
            raise ViewException(code="9008", message="ExchangeRate: Failed to load data.", errors=[])

        connection.close()
        return response

    def get_exchange_rate(self) -> Decimal:
        """
            Get Exchange rate for source and target and return the decimal value of the rate.
            :return: Decimal
        """

        exchange_rate = self._get()
        value = exchange_rate["rates"].get(self._target)

        if not value:
            raise ViewException(code="9009", message="ExchangeRate: Failed to load empty.", errors=[])

        return Decimal(value)
