"""
    Title: Purolator Track
    Description: This file will contain functions related to Purolator Track Apis.
    Created: December 11, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.utils import timezone
from zeep.exceptions import Fault

from api.apis.carriers.purolator.courier.endpoints.purolator_base import (
    PurolatorBaseApi,
)
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import TrackException
from api.globals.carriers import PUROLATOR
from api.models import Leg, CarrierAccount
from brain.settings import PURO_BASE_URL


class PurolatorTrack(PurolatorBaseApi):
    """
    Purolator Pickup Class
    """

    _version = "1.2"
    _service = None

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request, is_track=True)
        self.carrier_account = None
        self._response = {}

    @staticmethod
    def _process_track(response: dict) -> dict:
        """
        Process puro tracking for latest status, also get pod image for shipment.
        :param response: Puro Response
        :return: tracking details dict
        """

        if not response:
            raise Exception(f"No Response: {str(response)}")

        scans = response["TrackingInformation"][0]["Scans"]

        if not scans:
            raise Exception("No Scans")

        track_details = scans["Scan"][0]

        delivered_datetime = datetime.datetime(
            year=1, month=1, day=1, tzinfo=timezone.utc
        )

        if track_details["ScanType"] == "Other":
            status = "InTransit"
        elif track_details["ScanType"] == "ProofOfPickUp":
            status = "PickedUp"
        else:
            status = track_details["ScanType"]

        details = f'{track_details["Description"]} {track_details["Depot"]["Name"]}'

        if status == "OnDelivery":
            if track_details["ScanDetails"]["DeliveryAddress"]:
                address = " ".join(
                    track_details["ScanDetails"]["DeliveryAddress"].split()
                )
            else:
                address = ""

            details = f"{details} to {address}"
        elif status == "Delivery":
            scan_details = track_details["ScanDetails"]

            if scan_details["DeliveryAddress"]:
                address = " ".join(scan_details["DeliveryAddress"].split())
            else:
                address = ""

            details = f'{details}, to {scan_details["DeliverySignature"]} at {address}'
            delivered_datetime = datetime.datetime.strptime(
                track_details["ScanDate"], "%Y-%m-%d"
            )

        # TODO - Check Imagine for POD and other images

        if status == "Delivery":
            code = "Delivered"
        elif status in ["DeliveryException", "Undeliverable", "UndeliverableScan"]:
            code = "DeliveryException"
        elif status == "OnDelivery" or "On vehicle for delivery" in details:
            code = "OutForDelivery"
        elif status in ["InTransit"]:
            code = "InTransit"
        elif status in ["PickedUp", "Picked Up", "ProofOfPickUp"]:
            code = "Pickup"
        else:
            code = status

        return {
            "delivered_datetime": delivered_datetime,
            "estimated_delivery_datetime": delivered_datetime,
            "status": code,
            "details": details,
        }

    def setup_track(self):
        """
        Setup track connection for Purolator.
        :return:
        """
        self.create_connection(wsdl_path="TrackingService.wsdl", version=self._version)
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v1}TrackingServiceEndpoint",
            f"{PURO_BASE_URL}/EWS/V1/Tracking/TrackingService.asmx",
        )

    def _post(self, pin: str) -> dict:
        """
        Send Track request to purolator.
        :return:
        """
        try:
            response = self._service.TrackPackagesByPin(
                _soapheaders=[
                    self._build_request_context(
                        reference=f"TrackPackagesByPin - {pin}", version=self._version
                    )
                ],
                PINs=[{"PIN": {"Value": pin}}],
            )
        except Fault as e:
            CeleryLogger().l_warning.delay(
                location="purolator_track.py line: 98",
                message=str(
                    {"api.error.purolator.track": f"Zeep Failure: {str(e.detail)}"}
                ),
            )
            raise Exception(f"Zeep Failure:: {str(e)}") from e

        return response["body"]["TrackingInformationList"]

    def track(self, leg: Leg) -> dict:
        """
        Track purolator shipment.
        :param leg:
        :return:
        """

        try:
            # Get account for sub account
            self.carrier_account = CarrierAccount.objects.get(
                subaccount=leg.shipment.subaccount, carrier__code=PUROLATOR
            )
        except ObjectDoesNotExist:
            # Get default account
            self.carrier_account = CarrierAccount.objects.get(
                carrier__code=PUROLATOR, subaccount__is_default=True
            )

        self._account_number = self.carrier_account.account_number.decrypt()
        self._password = self.carrier_account.password.decrypt()
        self._key = self.carrier_account.api_key.decrypt()
        self.setup_track()

        try:
            response = self._post(pin=leg.tracking_identifier)
        except (Exception, KeyError) as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="purolator_ship.py line: 152",
                message=f"Purolator track: {str(e)}, Data: {str(leg)}",
            )
            raise TrackException(
                {
                    "api.error.purolator.track": f"Track Failure: Please contact support. {str(e)}"
                }
            ) from e

        try:
            track_details = self._process_track(response=response)
        except Exception as e:
            raise TrackException(
                {"api.error.purolator.track": f"Track Failure: Carrier Issue. {str(e)}"}
            ) from e

        if not track_details:
            raise TrackException(
                {"api.error.purolator.track": "Track Failure: No Tracking Details."}
            )

        track_details["leg"] = leg

        connection.close()
        return track_details
