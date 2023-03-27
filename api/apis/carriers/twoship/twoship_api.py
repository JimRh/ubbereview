"""
    Title: TwoShip Api
    Description: This file will contain functions related to TwoShip Api.
    Created: Jan 10, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.twoship.endpoints.twoship_pickup_v2 import TwoShipPickup
from api.apis.carriers.twoship.endpoints.twoship_rate_v2 import TwoShipRate
from api.apis.carriers.twoship.endpoints.twoship_ship_v2 import TwoShipShip
from api.apis.carriers.twoship.endpoints.twoship_track_v2 import TwoShipTrack

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    RateException,
    ShipException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import UPS, DHL


class TwoShipApi(BaseCarrierApi):
    """
    TwoShip Abstract Interface.
    """

    _carrier_api_name = "TwoShip"
    _carrier_ids = [UPS, DHL]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        TwoShip Rate Api
        :return: TwoShip rates in ubbe format.
        """

        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = TwoShipRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="twoship_api.py line: 39", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="twoship_api.py line: 39", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        TwoShip Shipping Api
        :return: TwoShip shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = TwoShipShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="twoship_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.twoship.ship": e.message}) from e

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
        TwoShip Pickup Api
        :return: TwoShip pickup response in ubbe format
        """
        self._check_active()

        try:
            pickup = TwoShipPickup(ubbe_request=self._ubbe_request).pickup()
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
            status = TwoShipTrack(ubbe_request=self._ubbe_request).track()
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="twoship_api.py",
                message=str(e.message),
            )
            raise ViewException({"api.error.twoship.track": e.message}) from e

        return status

    def cancel(self) -> dict:
        """
        TwoShip Void Api
        :return: TwoShip void response in ubbe format
        """
        self._check_active()

        try:
            void = TwoShipShip(ubbe_request=self._ubbe_request).void()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="twoship_api.py line: 54", message=e.message
            )
            void = {"is_canceled": False, "message": "Shipment failed to cancel."}

        return void

    def cancel_pickup(self) -> dict:
        """
        TwoShip Pickup Void Api
        :return: TwoShip void response in ubbe format
        """
        self._check_active()

        try:
            void = TwoShipPickup(ubbe_request=self._ubbe_request).void()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="twoship_api.py",
                message=f"2Ship Void (L65): {str(e.message)}",
            )
            void = {"is_canceled": False, "message": "Pickup failed to cancel."}

        return void
