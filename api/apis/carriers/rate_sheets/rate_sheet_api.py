"""
Title: Rate Sheet Api
Description: This file will contain functions related to Rate Sheet Api.
Created: Jan 30, 2023
Author: Carmichael
Edited By:
Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.rate_sheets.endpoints.rs_email_v2 import RateSheetEmail
from api.apis.carriers.rate_sheets.endpoints.rs_rate_v2 import RateSheetRate
from api.apis.carriers.rate_sheets.endpoints.rs_ship_v2 import RateSheetShip

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    PickupException,
    ViewException,
)
from api.globals.carriers import RATE_SHEET_CARRIERS


class RateSheetApi(BaseCarrierApi):
    """
    Rate Sheet Abstract Interface.
    """

    _carrier_api_name = "RateSheets"
    _carrier_ids = RATE_SHEET_CARRIERS

    _package_limit = 9

    def __init__(self, ubbe_request: dict, is_sealift: bool = False) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._is_sealift = is_sealift

    def rate(self) -> list:
        """
        Rate Sheet Rate Api
        :return: Rate Sheet rates in ubbe format.
        """
        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = RateSheetRate(
                ubbe_request=self._ubbe_request, is_sealift=self._is_sealift
            ).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="rate_sheet_api.py line: 70", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="rate_sheet_api.py line: 74", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Rate Sheet Api
        :return: Rate Sheet ship in ubbe format.
        """
        self._check_active()

        try:
            response = RateSheetShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="rate_sheet_api.py line: 54", message=e.message
            )
            raise ShipException({"api.error.rate_sheet.ship": e.message}) from e

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        Rate Sheet Ship Api
        :return: Rate Sheet email for pickup in ubbe format.
        """
        pickup = {
            "pickup_id": "",
            "pickup_message": "Pickup has been requested",
            "pickup_status": "Success",
        }

        self._check_active()

        try:
            RateSheetEmail(ubbe_request=self._ubbe_request).manual_email()
        except PickupException as e:
            CeleryLogger.l_critical(
                location="yrc_api.py", message=f"YRC Pickup (L83): {str(e.message)}"
            )

            pickup = self._default_pickup_error

        connection.close()
        return pickup

    def track(self) -> dict:
        """
        Rate Sheet Tracking Api
        :return: None
        """
        return {}
