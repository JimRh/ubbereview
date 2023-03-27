"""
    Title: Cargojet Api
    Description: This file will contain functions related to cargojet Api.
    Created: Sept 27, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from api.apis.carriers.base_carrier_api import BaseCarrierApi
from api.apis.carriers.cargojet.endpoints.cj_document import CargojetDocument
from api.apis.carriers.cargojet.endpoints.cj_ship import CargojetShip
from api.apis.carriers.cargojet.endpoints.cj_track import CargojetTrack
from api.apis.carriers.rate_sheets.rate_sheet_api import RateSheetApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import (
    ShipException,
    RateException,
    TrackException,
    RateExceptionNoEmail,
    PickupException,
    ViewException,
)
from api.globals.carriers import CARGO_JET
from api.models import ProBillNumber


class Cargojet(BaseCarrierApi):
    """
    Cargojet Abstract Interface.
    """

    _carrier_api_name = "Cargojet"
    _carrier_ids = [CARGO_JET]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def rate(self) -> list:
        """
        Cargojet Rating Api
        :return:
        """
        rates = []

        try:
            self._check_active()
        except ViewException:
            return rates

        try:
            rates = RateSheetApi(
                ubbe_request=self._ubbe_request, is_sealift=False
            ).rate()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="cargojet_api.py line: 33",
                message=str({"api.error.cargojet.rate": e.message}),
            )
            return rates
        except RateExceptionNoEmail:
            return rates

        return rates

    def ship(self, order_number: str = "") -> dict:
        """
        Cargojet Shipping Api
        :return: shipping response
        """
        self._check_active()

        now_date = datetime.datetime.now() + datetime.timedelta(seconds=60)
        cut_off_date = datetime.datetime.now().replace(hour=22, minute=30)  # 10:30 UTC

        if cut_off_date > now_date and self._ubbe_request["origin"]["base"] in [
            "YEG",
            "YYZ",
            "YHM",
        ]:
            try:
                response = CargojetShip(ubbe_request=self._ubbe_request).ship()
            except ShipException as e:
                CeleryLogger().l_critical.delay(
                    location="cargojet_api.py line: 52", message=e.message
                )
                raise ShipException({"api.error.cargojet.ship": e.message}) from e

            try:
                self._ubbe_request["awb"] = response["tracking_number"]
                self._ubbe_request["bol"] = response["tracking_number"]
                documents = CargojetDocument(
                    ubbe_request=self._ubbe_request
                ).documents()
            except ShipException as e:
                raise ShipException(
                    {"api.error.cargojet.ship": f"{e.message} - {response}"}
                ) from e

            if not documents:
                raise ShipException(
                    {"api.error.cargojet.ship": "CJ Document (L66): No documents."}
                )

            response["documents"] = documents
        else:
            awb = ProBillNumber.objects.filter(
                carrier__code=CARGO_JET, available=True
            ).first()

            if not awb:
                raise ShipException({"api.cargojet.ship": "No available air waybills"})

            awb.available = False
            awb.save()
            self._ubbe_request["awb"] = awb.probill_number

            response = RateSheetApi(ubbe_request=self._ubbe_request).ship(
                order_number=""
            )

        return response

    def pickup(self):
        """
        Pickup Endpoint not supported for air carriers.
        :return:
        """
        raise PickupException({"cargojet_pickup": "Endpoint Not Support."})

    def track(self) -> dict:
        """
        Cargojet Tracking Api
        :return:
        """
        self._check_active()

        try:
            status = CargojetTrack(ubbe_request={}).track(leg=self._ubbe_request["leg"])
        except TrackException as e:
            CeleryLogger().l_warning.delay(
                location="cargojet_api.py line: 91", message=e.message
            )
            raise TrackException({"api.error.cargojet.track": str(e.message)}) from e

        return status
