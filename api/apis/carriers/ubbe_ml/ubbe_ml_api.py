"""
    Title: ubbe ML Carrier Api
    Description: This file will contain functions related to ubbe ML Carrier Api.
    Created: Jan 10, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_email import MLCarrierEmail
from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_rate import MLCarrierRate
from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_ship import MLCarrierShip
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    RateException,
    ShipException,
    PickupException,
    ViewException,
)
from api.globals.carriers import UBBE_ML


class UbbeMLApi(BaseCarrierApi):
    """
    ubbe ML Abstract Interface.
    """

    _carrier_api_name = "UBBEML"
    _carrier_ids = [UBBE_ML]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        ubbe ML Rate Api
        :return: ubbe ML rates in ubbe format.
        """
        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = MLCarrierRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="ubbe_ml_api.py line: 39", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="ubbe_ml_api.py line: 39", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        ubbe ML Shipping Api
        :return: ubbe ML shipping response in ubbe format.
        """
        self._check_active()

        try:
            response = MLCarrierShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="ubbe_ml_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.ubbe_ml.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["response"] = response
            response.update(self.pickup())

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        ubbe ML Pickup Api
        :return: ubbe ML pickup response in ubbe format
        """
        self._check_active()

        response = self._ubbe_request.pop("response")

        try:
            pickup = MLCarrierEmail(ubbe_request=self._ubbe_request).manual_email(
                ship_data=response
            )
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="ubbe_ml_api.py line: 65", message=str(e.message)
            )
            pickup = self._default_pickup_error

        return pickup

    def track(self) -> dict:
        """
        ubbe ML Tracking Api
        :return: ubbe ML tracking response in ubbe format.
        """

        return {}
