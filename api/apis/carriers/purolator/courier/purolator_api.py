"""
    Title: Purolator Api
    Description: This file will contain functions related to Purolator Api.
    Created: July 13, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.purolator.courier.endpoints.purolator_pickup import (
    PurolatorPickup,
)
from api.apis.carriers.purolator.courier.endpoints.purolator_rate import PurolatorRate
from api.apis.carriers.purolator.courier.endpoints.purolator_ship import PurolatorShip
from api.apis.carriers.purolator.courier.endpoints.purolator_track import PurolatorTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import PUROLATOR


class PurolatorApi(BaseCarrierApi):
    """
    Purolator Abstract Interface.
    """

    _carrier_api_name = "Purolator"
    _carrier_ids = [PUROLATOR]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        Purolator Rate Api
        :return: Purolator rates in ubbe format.
        """

        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = PurolatorRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="purolator_api.py line: 39", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_api.py line: 39", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Purolator Shipping Api
        :return: Purolator shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = PurolatorShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="purolator_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.purolator.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["tracking_number"] = response["tracking_number"]
            pickup = self.pickup()
            response.update(pickup)

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        Purolator Pickup Api
        :return: Purolator pickup response in ubbe format
        """
        self._check_active()

        try:
            pickup = PurolatorPickup(ubbe_request=self._ubbe_request).pickup()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="purolator_api.py line: 65", message=str(e.message)
            )
            pickup = {
                "pickup_id": "",
                "pickup_message": "Failed",
                "pickup_status": "Failed",
            }

        return pickup

    def track(self) -> dict:
        """
        Purolator Tracking Api
        :return: Purolator tracking response in ubbe format.
        """
        self._check_active()

        try:
            status = PurolatorTrack(ubbe_request={}).track(
                leg=self._ubbe_request["leg"]
            )
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="purolator_api.py",
                message=f"Purolator Track (L106): {str(e.message)}",
            )
            raise ViewException({"api.error.purolator.track": e.message}) from e

        return status

    def cancel(self) -> dict:
        """
        Purolator Void Api
        :return: Purolator void response in ubbe format
        """
        self._check_active()

        try:
            void = PurolatorShip(ubbe_request=self._ubbe_request).void(
                pin=self._ubbe_request["tracking_number"]
            )
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="purolator_api.py line: 54", message=e.message
            )
            void = {"is_canceled": False, "message": "Shipment Cancel."}

        return void

    def cancel_pickup(self) -> dict:
        """
        Purolator Pickup Void Api
        :return: Purolator void response in ubbe format
        """
        self._check_active()

        try:
            void = PurolatorPickup(ubbe_request=self._ubbe_request).void(
                pin=self._ubbe_request["pickup_id"]
            )
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="purolator_api.py",
                message=f"Purolator Void (L65): {str(e.message)}",
            )
            void = {"is_canceled": False, "message": "Shipment failed to cancel."}

        return void
