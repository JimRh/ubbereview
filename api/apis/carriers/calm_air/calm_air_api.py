"""
    Title: Calm Api
    Description: This file will contain functions related to Calm Api.
    Created: June 23, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.calm_air.endpoints.calm_air_rate import CalmAirRate
from api.apis.carriers.calm_air.endpoints.calm_air_ship import CalmAirShip
from api.apis.carriers.calm_air.endpoints.calm_air_track import CalmAirTrack
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    RateException,
    ShipException,
    TrackException,
    ViewException,
    PickupException,
)
from api.globals.carriers import CALM_AIR


class CalmAirApi(BaseCarrierApi):
    """
    Calm Air Abstract Interface.
    """

    _carrier_api_name = "CalmAir"
    _carrier_ids = [CALM_AIR]

    _package_limit = 5

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _check_package_limit(self) -> None:
        """
        Check package amount for carrier limit of 5.
        """

        if len(self._ubbe_request["packages"]) > self._package_limit:
            connection.close()
            raise ViewException("Calm Air Ship (L54): Over max packages (5).")

    def rate(self) -> list:
        """
        Calm Air Rate Api
        :return: Calm Air rates in ubbe format.
        """

        rates = []

        try:
            self._check_active()
            self._check_package_limit()
        except ViewException:
            return rates

        try:
            rates = CalmAirRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_api.py line: 39", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_api.py line: 39", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Calm Air Shipping Api
        :return: Calm Air shipping response in ubbe format.
        """
        self._check_active()

        self._check_package_limit()

        try:
            response = CalmAirShip(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="calm_air_api.py line: 55", message=str(e.message)
            )
            raise ShipException({"api.error.calm_air.ship": e.message}) from e

        connection.close()
        return response

    def pickup(self):
        """
        Pickup Endpoint not supported for air carriers.
        :return:
        """
        raise PickupException({"calm_air_pickup": "Endpoint Not Support."})

    def track(self) -> dict:
        """
        Calm Air Tracking Api
        :return:
        """
        self._check_active()

        try:
            status = CalmAirTrack().track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            CeleryLogger().l_warning.delay(
                location="calm_air_api.py line: 91", message=e.message
            )
            raise TrackException({"api.error.calm_air.track": str(e.message)}) from e

        return status
