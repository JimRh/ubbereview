"""
    Title: Purolator Pickup
    Description: This file will contain functions related to Purolator Pickup Apis.
    Created: December 4, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection
from lxml import etree
from zeep.exceptions import Fault

from api.apis.carriers.purolator.courier.endpoints.purolator_base import (
    PurolatorBaseApi,
)
from api.apis.carriers.purolator.courier.helpers.shipment import PurolatorShipment
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException, PickupException
from api.utilities.date_utility import DateUtility
from brain.settings import PURO_BASE_URL


# TODO - Re look at Error response from validate and Pickup


class PurolatorPickup(PurolatorBaseApi):
    """
    Purolator Pickup Class
    """

    _version = "1.2"
    _service = None

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self.create_connection(wsdl_path="PickUpService.wsdl", version=self._version)
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v1}PickUpServiceEndpoint",
            f"{PURO_BASE_URL}/EWS/V1/PickUp/PickUpService.asmx",
        )

        self._puro_shipment = PurolatorShipment(
            is_rate=False, ubbe_request=self._ubbe_request
        )
        self._order_number = self._ubbe_request["order_number"]

        self._response = {}

    @staticmethod
    def _build_ship_summary(request: dict) -> list:
        """
        Build purolator ship summary soap object.
        :param request: Puro Shipment soap object, reuse already built items.
        :return:
        """

        destination = request["ReceiverInformation"]["Address"]["Country"]

        if destination not in ("US", "CA"):
            code = "INT"
        elif destination == "US":
            code = "USA"
        else:
            code = "DOM"

        return [
            {
                "ShipmentSummaryDetails": {
                    "ShipmentSummaryDetail": {
                        "DestinationCode": code,
                        "TotalPieces": request["PackageInformation"]["TotalPieces"],
                        "TotalWeight": request["PackageInformation"]["TotalWeight"],
                    }
                }
            }
        ]

    def _build_pickup_instructions(self, is_next_day: bool = False) -> dict:
        """
        Build purolator pickup instructions soap object.
        :return:
        """

        if is_next_day:
            nbd = DateUtility().next_business_day(
                self._ubbe_request["origin"]["country"],
                self._ubbe_request["origin"]["province"],
                self._ubbe_request["pickup"]["date"],
            )

            return {
                "Date": nbd,
                "AnyTimeAfter": "08:00",
                "UntilTime": "18:00",
                "PickUpLocation": "FrontDesk",
            }

        return {
            "Date": self._ubbe_request["pickup"]["date"].strftime("%Y-%m-%d"),
            "AnyTimeAfter": self._ubbe_request["pickup"]["start_time"],
            "UntilTime": self._ubbe_request["pickup"]["end_time"],
            "PickUpLocation": "FrontDesk",
        }

    def _build_request(self, is_next_day: bool = False) -> dict:
        """
        Build purolator pickup request.
        :return:
        """

        try:
            request = self._puro_shipment.shipment(account_number=self._account_number)
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_pickup.py line: 115",
                message=f"Error: {str(e)}, Data: {str(e)}",
            )
            connection.close()
            errors = [{"pickup": "Pickup Request Fail: Please contact support."}]
            raise PickupException(
                code="", message="Pickup Build Request Failed.", errors=errors
            ) from e

        return {
            "_soapheaders": [
                self._build_request_context(
                    reference=f"SchedulePickUp - {self._order_number}",
                    version=self._version,
                )
            ],
            "BillingAccountNumber": self._account_number,
            "PickupInstruction": self._build_pickup_instructions(
                is_next_day=is_next_day
            ),
            "Address": request["SenderInformation"]["Address"],
            "ShipmentSummary": self._build_ship_summary(request=request),
            "NotificationEmails": {"NotificationEmail": "no-rely@ubbe.com"},
        }

    def _post(self, request: dict) -> dict:
        """
        Send Create Pickup request to purolator.
        :return:
        """

        try:
            response = self._service.SchedulePickUp(**request)
        except (Fault, ValueError) as e:
            error = f"SchedulePickUp Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_critical.delay(
                location="purolator_pickup.py line: 110",
                message=str({"api.error.purolator.pickup": f"{error}"}),
            )
            response = {"body": {"PickUpConfirmationNumber": ""}}
        CeleryLogger().l_critical.delay(
            location="CDHSIUAVHAUDVHIQUDV",
            message=str(response),
        )
        pickup_id = response["body"]["PickUpConfirmationNumber"]
        message = "Booked"
        status = "Success"

        if not pickup_id:
            message = "Pickup Failed"
            status = "Failed"

        return {
            "pickup_id": pickup_id,
            "pickup_message": message,
            "pickup_status": status,
        }

    def _validate_post(self, request: dict) -> bool:
        """
        Send Void Shipment request to purolator.
        :return:
        """

        try:
            response = self._service.ValidatePickUp(**request)
        except (Fault, ValueError) as e:
            error = f"ValidatePickUp Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_pickup.py line: 167",
                message=str({"api.error.purolator.pickup.validate": f"{error}"}),
            )

            errors = [{"pickup": f"Validate Failure: {e.message}."}]
            raise PickupException(
                code="", message="Pickup Validated Request Failed", errors=errors
            ) from e

        return True

    def _void_post(self, pin: str) -> None:
        """
        Send Void Shipment request to purolator.
        :return:
        """

        try:
            response = self._service.VoidPickUp(
                _soapheaders=[
                    self._build_request_context(
                        reference=f"VoidPickUp - {pin}", version="1.2"
                    )
                ],
                PickUpConfirmationNumber=pin,
            )
        except (Fault, ValueError) as e:
            error = f"VoidPickUp Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_pickup.py line: 155",
                message=str({"api.error.purolator.pickup.void": f"{error}"}),
            )

            errors = [{"pickup": f"Void Failure: {str(e)}."}]
            raise PickupException(
                code="", message="Pickup Void Request Failed", errors=errors
            ) from e

        if "PickUpVoided" in response["body"]:
            is_void = response["body"]["PickUpVoided"]
        else:
            is_void = False

        self._response = {"is_canceled": is_void, "message": ""}

    def pickup(self, is_next_day: bool = False) -> dict:
        """
        Create Purolator Pickup.
        :return:
        """

        try:
            request = self._build_request(is_next_day=is_next_day)
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_pickup.py line: 234",
                message=f"Purolator Pickup: {str(e)}",
            )
            connection.close()
            errors = [{"pickup": f"Build Failure: {str(e)}."}]
            raise PickupException(
                code="", message="Pickup Build Request Failed", errors=errors
            ) from e

        try:
            is_valid = self._validate_post(request=request)
        except KeyError as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="purolator_pickup.py line: 244",
                message=f"Purolator Pickup: {str(e)}, Data: {str(request)}",
            )
            errors = [{"pickup": f"KeyError: {str(e)}."}]
            raise PickupException(
                code="", message="Pickup Validate KeyError", errors=errors
            ) from e

        if not is_valid:
            errors = [{"pickup": "Shipping Failure: Shipment not valid."}]
            raise PickupException(
                code="", message="Shipping Failure: Shipment not valid.", errors=errors
            )

        pickup = self._post(request=request)

        return pickup

    def void(self, pin: str) -> dict:
        """
        Void Purolator Pickup.
        :return:
        """

        try:
            self._void_post(pin=pin)
        except (ShipException, KeyError) as e:
            CeleryLogger().l_critical.delay(
                location="purolator_pickup.py line: 273",
                message=f"Purolator Pickup: {str(e)}, Data: {pin}",
            )
            errors = [{"pickup": "Void Failure: Please contact support."}]
            raise PickupException(
                code="", message="Void Failure: Please contact support.", errors=errors
            ) from e

        return self._response
