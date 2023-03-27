"""
    Title: DayRoss Ship
    Description: This file will contain functions related to Day Ross and Sameday Shipping..
    Created: July 13, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64

from django.db import connection
from lxml import etree
from zeep import xsd
from zeep.exceptions import Fault

from api.apis.carriers.day_ross_v2.endpoints.day_ross_api_v2 import DayRossAPI
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException
from api.globals.project import DOCUMENT_TYPE_OTHER_DOCUMENT
from api.models import API


class DayRossPickup(DayRossAPI):
    def __init__(self, ubbe_request: dict) -> None:
        super(DayRossPickup, self).__init__(ubbe_request=ubbe_request)
        self._request = None
        self._response = {"pickup_number": "", "pickup_label": ""}

    def _build_request(self):
        """
        Format main body for shipment request.
        :return:
        """

        ready_time, close_time = self._create_pickup()

        data = {
            "ShipperAddress": self._create_address(self._origin),
            "ConsigneeAddress": self._create_address(self._destination),
            "BillToAccount": self._account_number,
            "Items": self._create_items(self._ubbe_request["packages"]),
            "ShipmentType": self._shipment_type,
            "PaymentType": self._payment_type,
            "MeasurementSystem": self._measurement_system,
            "Division": self._division,
            "ExpiryDate": self._expiry_date,
            "ReadyTime": ready_time,
            "ClosingTime": close_time,
            "ShipmentStatus": {
                "OrderEntryState": "ReadyForPickup",
                "RowVersion": xsd.SkipValue,
                "DataActions": xsd.SkipValue,
                "InternalStatus": xsd.SkipValue,
            },
            "ServiceLevel": self._ubbe_request["service_code"],
            "SpecialInstructions": self._ubbe_request.get("special_instructions", ""),
            "ReferenceNumbers": self._create_references(),
        }
        return self._dr_ns0.Shipment(**data)

    def _format_response(self, response) -> None:
        """
        Format day ross response into ubbe response.
        :param response: SOAP response
        :return:
        """

        self._response = {
            "pickup_number": response["OrderNumber"],
            "pickup_message": "Booked",
            "pickup_status": "Success",
            "pickup_label": {
                "document": base64.b64encode(response["BolBuffer"]).decode("ascii"),
                "type": DOCUMENT_TYPE_OTHER_DOCUMENT,
            },
        }

    def _post(self, request):
        """
        Send shipment Request to Day Ross to pickup.
        :param request: SOAP shipment request
        :return: response
        """

        try:
            response = self._dr_client.service.CreatePickup2(
                division=self._division,
                emailAddress=self._username,
                password=self._password,
                shipment=request,
                language="EN",
            )
        except Fault as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_ship.py line: 161",
                message=str(
                    {"api.error.dr.ship": "Zeep Failure: {}".format(e.message)}
                ),
            )
            CeleryLogger().l_info.delay(
                location="day_ross_ship.py line: 161",
                message="Day and Ross Ship request data: {}".format(
                    etree.tounicode(self._dr_history.last_sent["envelope"])
                ),
            )
            CeleryLogger().l_info.delay(
                location="day_ross_ship.py line: 161",
                message="Day and Ross Ship response data: {}".format(
                    etree.tounicode(self._dr_history.last_received["envelope"])
                ),
            )

            raise ShipException(
                {"api.error.dr.ship": "Could not ship D&R, request error"}
            )

        return response

    def pickup(self) -> dict:
        """
        Pickup Day Ross shipment.
        :return: pickup details
        """

        if not API.objects.get(name="DayAndRoss").active:
            connection.close()
            raise ShipException({"api.error.dr.pickup": "D&R api not active"})

        try:
            request = self._build_request()
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_pickup.py line: 273",
                message=str(
                    {"api.error.dr.pickup": "Pickup Request Failed: {}".format(str(e))}
                ),
            )
            raise ShipException(
                {
                    "api.error.dr.pickup": "Pickup Request Failed: Please contact support."
                }
            )

        try:
            response = self._post(request=request)
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_pickup.py line: 273",
                message=str(
                    {"api.error.dr.pickup": "Pickup Failure: {}".format(str(e))}
                ),
            )

            raise ShipException(
                {"api.error.dr.pickup": "Pickup Failure: Please contact support."}
            )

        try:
            self._format_response(response=response)
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_pickup.py line: 284",
                message=str(
                    {"api.error.dr.pickup": "Pickup Format Error:: {}".format(str(e))}
                ),
            )
            raise ShipException(
                {"api.error.dr.pickup": "Pickup Format Error: Please contact support."}
            )

        return self._response
