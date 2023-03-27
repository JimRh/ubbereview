"""
Title: Skyline Api
Description: This file will contain functions related to Skyline Api.
Created: February 3, 2023
Author: Carmichael
Edited By:
Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.skyline.endpoints.skyline_rate_v3 import SkylineRate
from api.apis.carriers.skyline.endpoints.skyline_ship_v3 import SkylineShip
from api.apis.carriers.skyline.endpoints.skyline_track_v3 import SkylineTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    RateException,
    ShipException,
    TrackException,
    PickupException,
    ViewException,
)
from api.globals.carriers import CAN_NORTH


class SkylineApi(BaseCarrierApi):
    """
    Skyline Abstract Interface.
    """

    _carrier_api_name = "Skyline"
    _carrier_ids = [CAN_NORTH]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._ubbe_request = ubbe_request

    def rate(self) -> list:
        """
        Skyline Rate Api
        :return: Calm Air rates in ubbe format.
        """

        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = SkylineRate(gobox_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="skyline_api.py line: 39", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="skyline_api.py line: 39", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Skyline Shipping Api
        :return: Skyline shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = SkylineShip(gobox_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="skyline_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.skyline.ship": e.message}) from e

        connection.close()
        return response

    def pickup(self):
        """
        Pickup Endpoint not supported for air carriers.
        :return:
        """
        raise PickupException({"skyline_pickup": "Endpoint Not Support."})

    def track(self) -> dict:
        """
        Calm Air Tracking Api
        :return:
        """
        self._check_active()

        try:
            status = SkylineTrack().track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            CeleryLogger().l_warning.delay(
                location="skyline_api.py line: 91", message=e.message
            )
            raise TrackException({"api.error.skyline_air.track": str(e.message)}) from e

        return status
