"""
    Title: 2Ship Track api
    Description: This file will contain functions related to 2Ship Track Api.
    Created: January 11, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timezone

from django.db import connection

from api.apis.carriers.twoship.endpoints.twoship_base_v2 import TwoShipBase
from api.exceptions.project import RequestError, ViewException, TrackException


class TwoShipTrack(TwoShipBase):
    """
    2Ship Track Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._leg = self._ubbe_request["leg"]

    def _build_request(self) -> dict:
        """
        Build 2Ship Tracking request.
        :return:
        """

        return {
            "CarrierId": self._leg.carrier.code,
            "TrackingNumber": self._leg.tracking_identifier,
            "WS_Key": self._api_key,
        }

    def _format_response(self, response: dict) -> dict:
        """
        Format 2Ship latest tracking into ubbe format and return the results.
        :param response: 2Ship Tracking Respnse
        :return: Formatted Tracking dict
        """

        status = response["TrackingStatus"]
        details = response["TrackingStatusDescription"]
        est_delivery = response["EstimatedDeliveryDate"]

        if status in ["DeliveryException", "Undeliverable", "UndeliverableScan"]:
            code = "DeliveryException"
        elif "out for delivery" in details.lower():
            code = "OutForDelivery"
        elif status in ["PickedUp", "Picked Up", "ProofOfPickUp"]:
            code = "Pickup"
        else:
            code = status

        ret = {"leg": self._leg, "status": code, "details": details}

        if est_delivery != "0001-01-01T00:00:00":
            ret["estimated_delivery_datetime"] = datetime.strptime(
                est_delivery, "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)

        if code == "Delivered":
            ret["delivered_datetime"] = datetime.strptime(
                response["DeliveryDate"], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=timezone.utc)

        return ret

    def track(self) -> dict:
        """
        Get 2Ship Tracking and format it into ubbe format and save the tracking.
        :return: Tracking
        """

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise TrackException(f"2Ship Track (L367): {str(e)}") from e

        try:
            response = self._post(url=self._track_url, request=request)
        except ViewException as e:
            connection.close()
            raise TrackException(f"2Ship Track (L367): {e.message}") from e
        except RequestError as e:
            connection.close()
            raise TrackException(f"2Ship Track (L367): {str(e)}") from e

        if response["IsError"]:
            raise TrackException(f"2Ship Track (L367): {str(response)}")

        try:
            response = self._format_response(response=response["Data"])
        except KeyError as e:
            connection.close()
            raise TrackException(f"2Ship Track (L367): {str(e)}") from e

        return response
