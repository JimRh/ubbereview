"""
    Title: Action Express Api
    Description: This file will contain functions related to Action Express Api.
    Created: June 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from api.apis.carriers.action_express.endpoints.ac_rate import ActionExpressRate
from api.apis.carriers.action_express.endpoints.ac_document import ActionExpressDocument
from api.apis.carriers.action_express.endpoints.ac_ship import ActionExpressShip
from api.apis.carriers.action_express.endpoints.ac_track import ActionExpressTrack
from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    TrackException,
    RateExceptionNoEmail,
    ViewException,
)
from api.globals.carriers import ACTION_EXPRESS


class ActionExpress(BaseCarrierApi):
    """
    Action Express Abstract Interface.
    """

    _carrier_api_name = "ActionExpress"
    _carrier_ids = [ACTION_EXPRESS]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self.ubbe_request = ubbe_request

    def rate(self) -> list:
        """
         Action Express Rating Api
        :return:
        """
        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = ActionExpressRate(ubbe_request=self.ubbe_request).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="action_express_api.py line: 36",
                message=f"Source: AE\nType: Rate\nCode: {e.code}\nMessage: {e.message}\nErrors: {str(e.errors)}",
            )
            return rates
        except RateExceptionNoEmail:
            return rates

        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Action Express Shipping Api
        :return: shipping response
        """
        self._check_active()

        try:
            response = ActionExpressShip(ubbe_request=self.ubbe_request).ship(
                order_number=""
            )
        except ShipException as e:
            CeleryLogger().l_critical.delay(
                location="action_express_api.py line: 52",
                message=f"Source: AE\nType: Rate\nCode: {e.code}\nMessage: {e.message}\nErrors: {str(e.errors)}",
            )
            raise ShipException(code=e.code, message=e.message, errors=e.errors) from e

        try:
            documents = ActionExpressDocument(ubbe_request=self.ubbe_request).documents(
                order_id=response["carrier_api_id"]
            )
        except ShipException as e:
            raise ShipException(code=e.code, message=e.message, errors=e.errors) from e

        if not documents:
            raise ShipException(
                code="27206", message="AE Document (L66): No documents.", errors=[]
            )

        response["documents"] = documents

        return response

    def pickup(self):
        pass

    def track(self) -> dict:
        """
        Action Express Tracking Api
        :return:
        """
        self._check_active()

        try:
            status = ActionExpressTrack(ubbe_request={}).track(
                leg=self._ubbe_request["leg"]
            )
        except TrackException as e:
            CeleryLogger().l_warning.delay(
                location="action_express_api.py line: 91", message=e.message
            )
            raise TrackException(
                {"api.error.action_express.track": str(e.message)}
            ) from e

        return status
