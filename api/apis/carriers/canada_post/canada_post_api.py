"""
    Title: Canada Post Api
    Description: This file will contain functions related to Canada Post Api.
    Created: Feb 7, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.canada_post.abstraction.canadapost_pickup import CanadaPostPickup
from api.apis.carriers.canada_post.abstraction.canadapost_rate import CanadaPostRate
from api.apis.carriers.canada_post.abstraction.canadapost_ship import CanadaPostShip
from api.apis.carriers.canada_post.abstraction.canadapost_track import CanadaPostTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ViewException,
    RateException,
    ShipException,
    PickupException,
    TrackException,
)
from api.globals.carriers import CAN_POST


class CanadaPostApi(BaseCarrierApi):
    """
    Canada Post Abstract Interface.
    """

    _carrier_api_name = "CanadaPost"
    _carrier_ids = [CAN_POST]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        Canada Post Rate Api
        :return: Canada Post rates in ubbe format.
        """

        rates = []
        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = CanadaPostRate(world_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="canada_post_api.py line: 49", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="canada_post_api.py line: 49", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Canada Post Shipping Api
        :return: Canada Post shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = CanadaPostShip(world_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="canada_post_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"canada_post_api.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["tracking_number"] = response["tracking_number"]
            pickup = self.pickup()

            response["total"] += pickup.pop("total")
            response["taxes"] += pickup.pop("tax")
            response["surcharges_cost"] += pickup.pop("subtotal")
            response["tax_percent"] = (
                response["taxes"] / (response["total"] - response["taxes"]) * 100
            ).quantize(Decimal(".01"))

            response.update(pickup)

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        TwoShip Pickup Api
        :return: TwoShip pickup response in ubbe format
        """
        self._check_active()

        try:
            pickup = CanadaPostPickup(world_request=self._ubbe_request).create()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="twoship_api.py line: 65", message=str(e.message)
            )
            pickup = self._default_pickup_error

        return pickup

    def track(self) -> dict:
        """
        TwoShip Tracking Api
        :return: TwoShip tracking response in ubbe format.
        """
        self._check_active()

        try:
            status = CanadaPostTrack().track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="twoship_api.py",
                message=str(e.message),
            )
            raise ViewException({"api.error.twoship.track": e.message}) from e

        return status
