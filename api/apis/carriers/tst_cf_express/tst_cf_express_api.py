"""
Title: TST-CF Express Api
Description: This file will contain functions related to TST-CF Express Api.
Created: Jan 12, 2023
Author: Carmichael
Edited By:
Edited Date:
"""
from django.db import connection

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_bol_v2 import TstCfExpressBOL
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_rate_v2 import TstCfExpressRate
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_ship_v2 import TstCfExpressShip
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_track_v2 import TstCfExpressTrack

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    PickupException,
    TrackException,
    ViewException,
)
from api.globals.carriers import TST


class TSTCFExpressApi(BaseCarrierApi):
    """
    TST-CF Express Abstract Interface.
    """

    _carrier_api_name = "TstOverland"
    _carrier_ids = [TST]

    _package_limit = 9

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _check_package_limit(self) -> None:
        """
        Check package amount for carrier limit of 9.
        """

        if len(self._ubbe_request["packages"]) > self._package_limit:
            connection.close()
            raise ViewException("TST-CF (L54): Over max packages (9).")

    def rate(self) -> list:
        """
        TST-CF Express Rate Api
        :return: TST-CF Express rates in ubbe format.
        """
        rates = []

        try:
            self._check_active()
            self._check_package_limit()
        except ViewException:
            return rates

        try:
            rates = TstCfExpressRate(ubbe_request=self._ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="tst_cf_express_api.py line: 70", message=str(e.message)
            )
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="tst_cf_express_api.py line: 74", message=str(e)
            )

        connection.close()
        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        TST-CF Express Ship Api
        :return: TST-CF Express rates in ubbe format.
        """
        self._check_active()
        self._check_package_limit()

        if self._ubbe_request["is_pickup"]:
            # Ship and Pickup

            try:
                response = TstCfExpressShip(ubbe_request=self._ubbe_request).ship()
            except ShipException as e:
                connection.close()
                CeleryLogger().l_critical.delay(
                    location="tst_cf_express_api.py line: 95", message=str(e.message)
                )
                raise ShipException({"api.error.tst_cf_express.ship": e.message}) from e

            return response

        # Only Ship and no pickup
        try:
            response = TstCfExpressBOL(ubbe_request=self._ubbe_request).ship()
        except ShipException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="tst_cf_express_api.py line: 107", message=str(e.message)
            )
            raise ShipException({"api.error.tst_cf_express.ship": e.message}) from e

        return response

    def pickup(self) -> dict:
        """
        TST-CF Express Ship Api
        :return: TST-CF Express rates in ubbe format.
        """
        self._check_active()
        self._check_package_limit()

        try:
            pickup = TstCfExpressShip(ubbe_request=self._ubbe_request).ship()
            pickup = {
                "pickup_id": pickup["pickup_id"],
                "pickup_message": pickup["pickup_message"],
                "pickup_status": pickup["pickup_status"]
            }
        except PickupException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="tst_cf_express_api.py line: 126", message=str(e.message)
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
            status = TstCfExpressTrack(ubbe_request=self._ubbe_request).track()
        except TrackException as e:
            connection.close()
            CeleryLogger.l_critical(
                location="tst_cf_express_api.py",
                message=f"TST Track (L106): {str(e.message)}",
            )
            raise ViewException({"api.error.tst_cf_express.track": e.message}) from e

        return status
