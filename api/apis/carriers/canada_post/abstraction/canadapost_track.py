from datetime import datetime
from xml.etree.ElementTree import fromstring

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from requests.auth import HTTPBasicAuth


from api.exceptions.project import ViewException
from api.globals.carriers import CAN_POST
from api.globals.project import LOGGER, DEFAULT_TIMEOUT_SECONDS, HTTP_OK
from api.models import CarrierAccount, Leg


class CanadaPostTrack:
    _track_wsdl = "https://www.canadapost.ca/cpo/mc/assets/wsdl/developers/track.wsdl"

    def __init__(self):
        self._track_client = None
        self._rate_service = None
        self._carrier_account = None
        self._tracking_statuses = []

    def _post(self, leg, pin: str) -> None:
        url = f"https://soa-gw.canadapost.ca/vis/track/pin/{pin}/summary"

        response = requests.get(
            url,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            auth=HTTPBasicAuth(
                self._carrier_account.username.decrypt(),
                self._carrier_account.password.decrypt(),
            ),
        )

        if response.status_code != HTTP_OK:
            return

        try:
            xml_response = fromstring(response.text)
            data = xml_response[0]
        except Exception:
            raise Exception

        date = ""
        description = ""
        location = ""
        expected_delivery_date = ""
        event_type = ""
        actual_delivery_date = ""

        for child in data:
            if child.tag == "{http://www.canadapost.ca/ws/track}event-date-time":
                date = child.text
                date_parts = date.split(":")
                date = date_parts[0]
            elif child.tag == "{http://www.canadapost.ca/ws/track}event-description":
                description = child.text
            elif child.tag == "{http://www.canadapost.ca/ws/track}event-location":
                location = child.text
            elif (
                child.tag == "{http://www.canadapost.ca/ws/track}expected-delivery-date"
            ):
                expected_delivery_date = child.text
            elif child.tag == "{http://www.canadapost.ca/ws/track}event-type":
                event_type = child.text
            elif child.tag == "{http://www.canadapost.ca/ws/track}actual-delivery-date":
                actual_delivery_date = child.text

        detail = f"{description}, {location}."

        if expected_delivery_date:
            detail += f" Est Delivery {expected_delivery_date}"

        if event_type == "DELIVERED":
            code = "Delivered"
        elif event_type in ["OUT", "ATTEMPTED"]:
            code = "OutForDelivery"
        elif event_type in ["INFO", "VEHICLE_INFO"]:
            code = "InTransit"
        elif event_type in ["INDUCTION", "PR_RECEIVED"]:
            code = "Pickup"
        else:
            code = "Created"

        tracking = {
            "leg": leg,
            "estimated_delivery_datetime": datetime.strptime(date, "%Y%m%d").replace(
                tzinfo=timezone.utc
            ),
            "status": code,
            "details": detail,
        }

        if actual_delivery_date:
            tracking["delivered_datetime"] = datetime.strptime(
                actual_delivery_date, "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)

        self._tracking_statuses.append(tracking)

    def track(self, leg: Leg) -> dict:
        try:
            # Get account for sub account
            self._carrier_account = CarrierAccount.objects.get(
                subaccount=leg.shipment.subaccount, carrier__code=CAN_POST
            )
        except ObjectDoesNotExist:
            # Get default account
            self._carrier_account = CarrierAccount.objects.get(
                carrier__code=CAN_POST, subaccount__is_default=True
            )

        tracking_identifiers = leg.tracking_identifier
        pins = tracking_identifiers.split(",")

        for pin in pins:
            try:
                self._post(leg, pin)
            except Exception as e:
                LOGGER.critical(str(e))
                continue

        if not self._tracking_statuses:
            raise ViewException(
                {
                    "canada_post.track.error": f"Tracking identifier: {pins} obtained a tracking error from TwoShip"
                }
            )

        data = self._tracking_statuses[0]

        for status in self._tracking_statuses:  # For every package
            if (
                status["estimated_delivery_datetime"]
                > status["estimated_delivery_datetime"]
            ):
                data = status

        return data
