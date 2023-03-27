"""
    Title: Manitoulin Tracking Api
    Description: This file will contain functions related to Manitoulin Tracking Apis.
    Created: January 3, 2022
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import datetime
from typing import Union

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi
from api.apis.carriers.manitoulin.endpoints.manitoulin_document import (
    ManitoulinDocument,
)
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, TrackException
from api.globals.carriers import MANITOULIN
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import Leg, ShipDocument, CarrierAccount


class ManitoulinTrack(ManitoulinBaseApi):
    """
    Manitoulin Track Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request, is_track=True)

    @staticmethod
    def _process_response(response: dict) -> dict:
        """
        Process Manitoulin tracking response for the latest status and format into ubbe shipment tracking status.
        :return: dict of latest tracking status
        """

        if not response.get("details"):
            raise TrackException("Manitoulin Track (L34): No Tracking status yet.")

        details = response["details"]

        status_message = ""
        code = "Created"
        shipment_left = details.get("shipment_left", "")
        shipment_arriving = details.get("shipment_arrived", "")
        shipment_at = details.get("shipment_at", "")

        if "Delivered" in details["delivery_code"]:
            status_message = f'Delivered on {details["delivered_on"]}.'
            code = "Delivered"

            if details.get("received_by"):
                status_message += f'Received by {details["received_by"]}.'

        elif shipment_left or shipment_arriving or shipment_at:
            if shipment_left:
                status_message += f"Left {shipment_left}. "
                code = "InTransit"

            if shipment_arriving:
                status_message += f"Arriving in {shipment_arriving}. "
                code = "InTransit"

            if shipment_at:
                status_message += f"Currently at {shipment_at}."
                code = "InTransit"

        if not status_message:
            status_message = "Waiting for status"

        ret = {
            "status": code,
            "details": f"{status_message.strip()}",
        }

        if details.get("eta_date"):
            try:
                ret["estimated_delivery_datetime"] = datetime.datetime.strptime(
                    details["eta_date"], "%Y-%m-%d"
                )
            except TrackException:
                pass

        if code == "Delivered":
            delivered_list = details["delivered_on"].split(" ")

            try:
                ret["delivered_datetime"] = datetime.datetime.strptime(
                    delivered_list[0], "%Y-%m-%d"
                )
            except TrackException:
                ret["delivered_datetime"] = datetime.datetime.now()

        return ret

    def _get_tracking(self, probill_number: str) -> Union[list, dict]:
        """
        Get request to manitoulin probill endpoint to get tracking status
        :param: probill number
        :return: response from manitoulin api endpoint
        """

        try:
            response = requests.get(
                url=f"{self._track}{probill_number}",
                headers=self._get_auth(),
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(
                None, {"url": self._track, "error": str(e), "data": probill_number}
            ) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": self._track, "data": probill_number})

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_critical.delay(
                location="man_base.py line: 116", message=f"{response.text}"
            )
            connection.close()
            raise RequestError(
                response,
                {"url": self._rate_url, "error": str(e), "data": probill_number},
            ) from e

        connection.close()
        return response

    def _get_carrier_account(self, sub_account) -> None:
        """
        Get carrier account to api key to track shipment with
        :param sub_account: ubbe sub account
        """

        try:
            # Get account for sub account
            self._carrier_account = CarrierAccount.objects.get(
                subaccount=sub_account, carrier__code=MANITOULIN
            )
        except ObjectDoesNotExist:
            # Get default account
            self._carrier_account = CarrierAccount.objects.get(
                carrier__code=MANITOULIN, subaccount__is_default=True
            )

        self._sub_account = sub_account
        self._account_number = self._carrier_account.account_number.decrypt()
        self._username = self._carrier_account.username.decrypt()
        self._password = self._carrier_account.password.decrypt()

    def track(self, leg: Leg) -> dict:
        """
        Track Manitoulin shipment
        :param leg: ubbe leg model
        :return: tracking status
        """

        if not leg.tracking_identifier:
            raise TrackException(f"YRC Track (L113): No Tracking ID,  Data: {str(leg)}")

        self._get_carrier_account(sub_account=leg.shipment.subaccount)

        try:
            response = self._get_tracking(probill_number=leg.tracking_identifier)
        except RequestError as e:
            connection.close()
            raise TrackException(
                f"YRC Track (L125): Track Failure  {str(e)},  Leg: {str(leg)}"
            ) from e

        status = self._process_response(response=response)
        status["leg"] = leg

        if status["status"] == "Delivered":
            pass
            # try:
            #     documents = ManitoulinDocument(ubbe_request={}).get_tracking_documents(
            #         tracking_number=leg.tracking_identifier
            #     )
            #
            #     for document in documents:
            #         ShipDocument.add_document(
            #             leg=leg,
            #             document=document["document"],
            #             doc_type=document["type"],
            #         )
            #
            # except TrackException as e:
            #     CeleryLogger.l_critical(
            #         location="manitoulin_track.py",
            #         message=f"Manitoulin Track (L195): {str(e)}",
            #     )
            #     return ret

        connection.close()
        return status
