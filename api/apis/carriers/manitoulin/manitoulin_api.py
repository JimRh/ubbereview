"""
    Title: Manitoulin Api
    Description: This file will contain functions related to Manitoulin Api.
    Created: June 23, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.manitoulin.endpoints.manitoulin_pickup import ManitoulinPickup
from api.apis.carriers.manitoulin.endpoints.manitoulin_rate import ManitoulinRate
from api.apis.carriers.manitoulin.endpoints.manitoulin_ship import ManitoulinShip
from api.apis.carriers.manitoulin.endpoints.manitoulin_track import ManitoulinTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import MANITOULIN
from api.models import Leg


class ManitoulinApi(BaseCarrierApi):
    """
    Manitoulin Abstract Interface.
    """

    _carrier_api_name = "Manitoulin"
    _carrier_ids = [MANITOULIN]

    _package_limit = 3

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _check_package_limit(self) -> None:
        """
        Check package amount for carrier limit of 3.
        """

        if len(self._ubbe_request["packages"]) > self._package_limit:
            connection.close()
            raise ViewException("Manitoulin (L54): Over max packages (3).")

    def rate(self) -> list:
        """
        Manitoulin Api
        :return: Manitoulin rates in ubbe format.
        """

        rates = []
        try:
            self._check_active()
            self._check_package_limit()
        except ViewException:
            return rates

        try:
            rates = ManitoulinRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="manitoulin_api.py line: 36",
                message=str({"api.error.manitoulin.rate": e.message}),
            )
            return rates

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Manitoulin Shipping Api
        :return: Manitoulin shipping response in ubbe format.
        """
        self._check_active()
        self._check_package_limit()

        try:
            response = ManitoulinShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="manitoulin_api.py line: 54", message=e.message
            )
            raise ShipException({"api.error.manitoulin.ship": e.message})

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["tracking_number"] = response["tracking_number"]
            response.update(self.pickup())

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        Manitoulin Freight Pickup Api
        :return: Manitoulin Freight pickup response in ubbe format
        """
        self._check_active()
        self._check_package_limit()

        try:
            pickup = ManitoulinPickup(ubbe_request=self._ubbe_request).pickup()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="yrc_api.py",
                message=f"Manitoulin Pickup (L65): {str(e.message)}",
            )
            pickup = {
                "pickup_id": "",
                "pickup_message": "Failed",
                "pickup_status": "Failed",
            }

        return pickup

    def track(self) -> dict:
        """
        Manitoulin Freight Tracking Api
        :return: Manitoulin Freight tracking response in ubbe format.
        """
        self._check_active()

        try:
            status = ManitoulinTrack(ubbe_request={}).track(
                leg=self._ubbe_request["leg"]
            )
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="manitoulin_api.py",
                message=f"Manitoulin Track (L106): {str(e.message)}",
            )
            raise ViewException({"api.error.manitoulin.track": e.message})

        return status
