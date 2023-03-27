"""
    Title: Day Ross Api
    Description: This file will contain functions related to Day Ross Api.
    Created: Jan 30, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.day_ross_v2.endpoints.day_ross_rate_v2 import DayRossRate
from api.apis.carriers.day_ross_v2.endpoints.day_ross_ship_v2 import DayRossShip
from api.apis.carriers.day_ross_v2.endpoints.day_ross_track_v2 import DayRossTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    RateException,
    ShipException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import DAY_N_ROSS, SAMEDAY


class DayRossApi(BaseCarrierApi):
    """
    Day Ross Abstract Interface.
    """

    _carrier_api_name = "DayAndRoss"
    _carrier_ids = [DAY_N_ROSS, SAMEDAY]

    _package_limit = 6

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _check_package_limit(self) -> None:
        """
        Check package amount for carrier limit of 9.
        """

        if len(self._ubbe_request["packages"]) > self._package_limit:
            connection.close()
            raise ViewException("DayAndRoss (L54): DayAndRoss over max packages (9).")

    def rate(self) -> list:
        """
        Day Ross Rate Api
        :return: Day Ross rates in ubbe format.
        """

        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = DayRossRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="day_ross_api.py line: 39", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="day_ross_api.py line: 39", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Day Ross Shipping Api
        :return: Day Ross shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = DayRossShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.day_ross.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["tracking_number"] = response["tracking_number"]
            self._ubbe_request["service_name"] = response["service_name"]
            pickup = self.pickup()
            response.update(pickup)

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        Day Ross Pickup Api
        :return: Day Ross pickup response in ubbe format
        """
        self._check_active()

        try:
            pickup = {
                "pickup_id": "",
                "pickup_message": "Booked",
                "pickup_status": "Success",
            }
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="day_ross_api.py line: 65", message=str(e.message)
            )
            pickup = self._default_pickup_error

        return pickup

    def track(self) -> dict:
        """
        Day Ross Tracking Api
        :return: Day Ross tracking response in ubbe format.
        """
        self._check_active()

        try:
            status = DayRossTrack().track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="day_ross_api.py",
                message=str(e.message),
            )
            raise ViewException({"api.error.day_ross.track": e.message}) from e

        return status
