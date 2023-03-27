"""
    Title: Cargojet Tracking Api
    Description: This file will contain functions related to Cargojet Tracking Apis.
    Created: Sept 27, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.carriers.cargojet.endpoints.cj_api import CargojetApi
from api.exceptions.project import RequestError, TrackException
from api.globals.carriers import CARGO_JET
from api.models import Leg, CarrierAccount


class CargojetTrack(CargojetApi):
    """
    Cargojet Track Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request, is_track=True)

    @staticmethod
    def _process_response(response: list) -> dict:
        """
        Process Cargojet tracking response for the latest status and format into ubbe shipment tracking status.
        :return: dict of latest tracking status
        """

        if len(response) == 0:
            raise TrackException("CJ Track (L34): No Tracking status yet.")

        status = response[-1]
        status_code = status["Status"]

        if status_code in ["CANCELED"]:
            code = "Canceled"
        elif status_code in ["DELIVERED"]:
            code = "Delivered"
        elif status_code in ["CARGO ARRIVED", "ARRIVED", "DEPARTED"]:
            code = "InTransit"
        elif status_code in ["ACCEPTED", "UNDO ACCEPTANCE"]:
            code = "Pickup"
        else:
            code = "Created"

        if status_code in ["DEPARTED"]:
            description = (
                f'{status_code.title()} {status["Station"]} on {status["Date"]} (UTC)'
            )
        else:
            description = f'{status_code.title()} in {status["Station"]} on {status["Date"]} (UTC)'

        ret = {"status": code, "details": description}

        if code == "Delivered":
            ret["delivered_datetime"] = (
                datetime.datetime.now().replace(microsecond=0).isoformat()
            )

        return ret

    def _get_carrier_account(self, sub_account) -> None:
        """
        Get carrier account to api key to track shipment with.
        :param sub_account: ubbe sub account
        """

        try:
            # Get account for sub account
            self._carrier_account = CarrierAccount.objects.get(
                subaccount=sub_account, carrier__code=CARGO_JET
            )
        except ObjectDoesNotExist:
            # Get default account
            self._carrier_account = CarrierAccount.objects.get(
                carrier__code=CARGO_JET, subaccount__is_default=True
            )

    def track(self, leg: Leg) -> dict:
        """
        Track Cargojet shipment.
        :param leg: ubbe leg model.
        :return:
        """

        self._get_carrier_account(sub_account=leg.shipment.subaccount)
        headers = {
            "P_CUSCOD": self._carrier_account.contract_number.decrypt(),
            "P_KEY": self._carrier_account.api_key.decrypt(),
            "User-Agent": "ubbe/1.40.0",
        }

        if not leg.tracking_identifier:
            raise TrackException(f"CJ Track (L92): No Tracking ID,  Data: {str(leg)}")

        airway_parts = leg.tracking_identifier.split("-")

        headers["P_AWBPRE"] = airway_parts[0]
        headers["P_AWBNUM"] = airway_parts[1]

        try:
            response = self._get(url=f"{self._url}/tracking_booking", headers=headers)
        except RequestError as e:
            connection.close()
            raise TrackException(
                f"CJ Track (L102): Track Failure  {str(e)},  Leg: {str(leg)}"
            ) from e

        if "Errors" in response:
            raise TrackException(
                f"CJ Track (L106): Track Failure  {str(response['Errors'])},  Leg: {str(leg)}"
            )

        status = self._process_response(response=response.get("TRACKING", []))
        status["leg"] = leg

        connection.close()
        return status
