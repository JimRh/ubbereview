"""
    Title: YRC Freight Api
    Description: This file will contain functions related to yrc freight Api.
    Created: January 17, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.yrc.endpoints.yrc_pickup import YRCPickup
from api.apis.carriers.yrc.endpoints.yrc_rate import YRCRate
from api.apis.carriers.yrc.endpoints.yrc_ship import YRCShip
from api.apis.carriers.yrc.endpoints.yrc_track import YRCTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import YRC


class YRCFreight(BaseCarrierApi):
    """
    YRC Freight Abstract Interface.
    """

    _carrier_api_name = "YRC"
    _carrier_ids = [YRC]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        YRC Rating Api
        :return: YRC rates in ubbe format.
        """
        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = YRCRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="yrc_api.py line: 37",
                message=str({"api.error.yrc.rate": e.message}),
            )
            return rates

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        YRC Shipping Api
        :return: shipping response
        """
        self._check_active()

        try:
            response = YRCShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="yrc_api.py line: 54", message=e.message
            )
            raise ShipException({"api.error.yrc.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            response.update(self.pickup())

        connection.close()
        return response

    def pickup(self):
        """
        YRC Pickup Api
        :return: shipping response
        """
        self._check_active()

        try:
            pickup = YRCPickup(ubbe_request=self._ubbe_request).pickup()
        except PickupException as e:
            CeleryLogger.l_critical(
                location="yrc_api.py", message=f"YRC Pickup (L83): {str(e.message)}"
            )

            pickup = self._default_pickup_error

        connection.close()
        return pickup

    def track(self) -> dict:
        """
        YRC Tracking Api
        :return:
        """
        self._check_active()

        try:
            status = YRCTrack().track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="yrc_api.py", message=f"YRC Track (L106): {str(e.message)}"
            )
            raise ViewException({"api.error.yrc.track": e.message}) from e

        return status
