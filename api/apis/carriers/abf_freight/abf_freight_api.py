"""
    Title: ABF Freight Api
    Description: This file will contain functions related to ABF Freight Api.
    Created: June 23, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection

from api.apis.carriers.abf_freight.endpoints.abf_pickup import ABFPickup
from api.apis.carriers.abf_freight.endpoints.abf_rate import ABFRate
from api.apis.carriers.abf_freight.endpoints.abf_ship import ABFShip
from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    PickupException,
    ViewException,
    TrackException,
)
from api.globals.carriers import ABF_FREIGHT


class ABFFreight(BaseCarrierApi):
    """
    ABF Freight Abstract Interface.
    """

    _carrier_api_name = "ABFFreight"
    _carrier_ids = [ABF_FREIGHT]

    _package_limit = 15

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._ubbe_request = ubbe_request

    def _check_package_limit(self) -> None:
        """
        Check package amount for carrier limit of 15.
        """

        if len(self._ubbe_request["packages"]) > self._package_limit:
            connection.close()
            raise ViewException("ABF Freight (L54): Over max packages (15).")

    def rate(self) -> list:
        """
        ABF Freight Rate Api
        :return: ABF Freight rates in ubbe format.
        """
        rates = []

        try:
            self._check_active()
            self._check_package_limit()
        except ViewException:
            return rates

        try:
            rates = ABFRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="abf_freight_api.py line: 70", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="abf_freight_api.py line: 74", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        ABF Freight Shipping Api
        :return: ABF Freight shipping response in ubbe format.
        """
        self._check_active()
        self._check_package_limit()

        try:
            response = ABFShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="abf_freight_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.abf_freight.ship": e.message}) from e

        # Call to book pickup here and add to response
        if self._ubbe_request["is_pickup"]:
            self._ubbe_request["tracking_number"] = response["tracking_number"]
            pickup = self.pickup()
            response.update(pickup)

        connection.close()
        return response

    def pickup(self) -> dict:
        """
        ABF Freight Pickup Api
        :return: ABF Freight pickup response in ubbe format
        """
        self._check_active()
        self._check_package_limit()

        try:
            pickup = ABFPickup(ubbe_request=self._ubbe_request).pickup()
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="abf_freight_api.py line: 65", message=str(e.message)
            )
            pickup = self._default_pickup_error

        return pickup

    def track(self) -> dict:
        """
        TST-CF Express Tracking Api
        :return: TST-CF Express tracking response in ubbe format.
        """
        self._check_active()

        try:
            status = {}
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="abf_freight_api.py",
                message=str(e.message),
            )
            raise ViewException({"api.error.abf_freight.track": e.message}) from e

        return status
