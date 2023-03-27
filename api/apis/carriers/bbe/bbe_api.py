"""
    Title: BBE Api
    Description: This file will contain functions related to BBE Api.
    Created: July 13, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.bbe.endpoints.bbe_email_v1 import BBEEmail
from api.apis.carriers.bbe.endpoints.bbe_rate_v1 import BBERate
from api.apis.carriers.bbe.endpoints.bbe_ship_v1 import BBEShip
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    RateException,
    ShipException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import BBE


class BBEApi(BaseCarrierApi):
    """
    BBE Api Abstract Interface.
    """

    _carrier_api_name = "BBE"
    _carrier_ids = [BBE]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        BBE Rate Api
        :return: BBE rates in ubbe format.
        """
        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = BBERate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="bbe_api.py line: 37", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="bbe_api.py line: 37", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        BBE Shipping Api
        :return: BBE shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = BBEShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="purolator_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.purolator.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["response"] = response
            pickup = self.pickup()
            response.update(pickup)

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        BBE Pickup Api
        :return: BBE pickup response in ubbe format
        """
        self._check_active()

        response = self._ubbe_request["response"]

        try:
            pickup = BBEEmail(
                ubbe_request=self._ubbe_request, response=response
            ).send_email()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="bbe_api.py line: 65", message=str(e.message)
            )
            pickup = self._default_pickup_error

        return pickup

    def track(self) -> None:
        """
        BBE Tracking Api -> Not Implemented
        :return: BBE tracking response in ubbe format.
        """

        raise TrackException({"bbe_track": "Endpoint Not Support."})
