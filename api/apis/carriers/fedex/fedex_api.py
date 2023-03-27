"""
Title: FedEx Api
Description: This file will contain functions related to Fedex Api.
Created: Jan 12, 2023
Author: Carmichael
Edited By:
Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.fedex.endpoints.fedex_pickup_api_v1 import FedExPickup
from api.apis.carriers.fedex.endpoints.fedex_rate_api_v1 import FedExRate
from api.apis.carriers.fedex.endpoints.fedex_ship_api_v1 import FedExShip
from api.apis.carriers.fedex.endpoints.fedex_track_api_v1 import FedExTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ViewException,
    RateException,
    ShipException,
    PickupException,
    TrackException,
)
from api.globals.carriers import FEDEX


class FedexApi(BaseCarrierApi):
    """
    FedEx Abstract Interface.
    """

    _carrier_api_name = "FedEx"
    _carrier_ids = [FEDEX]

    _package_limit = 99

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _check_package_limit(self) -> None:
        """
        Check package amount for carrier limit of 99.
        """

        if len(self._ubbe_request["packages"]) > self._package_limit:
            connection.close()
            raise ViewException("FedEx (L54): Over max packages (99).")

    def rate(self) -> list:
        """
        FedEx Rate Api
        :return: FedEx rates in ubbe format.
        """

        rates = []

        try:
            self._check_active()
            self._check_package_limit()
        except ViewException:
            return rates

        try:
            rates = FedExRate(gobox_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="fedex_api.py line: 70", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="fedex_api.py line: 74", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        FedEx Shipping Api
        :return: FedEx shipping response in ubbe format
        """
        self._check_active()
        self._check_package_limit()

        try:
            response = FedExShip(gobox_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="fedex_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"fedex_api.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["tracking_number"] = response["tracking_number"]
            pickup = self.pickup()
            response.update(pickup)

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        FedEx Pickup Api
        :return: FedEx pickup response in ubbe format
        """
        self._check_active()

        try:
            pickup = FedExPickup(gobox_request=self._ubbe_request).pickup()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="fedex_api.py line: 65", message=str(e.message)
            )
            pickup = self._default_pickup_error

        return pickup

    def track(self) -> dict:
        """
        FedEx Tracking Api
        :return: FedEx tracking response in ubbe format.
        """
        self._check_active()

        try:
            status = FedExTrack().track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="fedex_api.py",
                message=str(e.message),
            )
            raise ViewException({"fedex_api.track": e.message}) from e

        return status
