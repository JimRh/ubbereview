"""
    Title: Purolator Rate
    Description: This file will contain functions related to Purolator Rate Apis.
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
from api.apis.carriers.purolator.courier.endpoints.purolator_documents import (
    PurolatorDocument,
)
from api.apis.carriers.purolator.courier.endpoints.purolator_rate import PurolatorRate
from api.apis.carriers.purolator.courier.helpers.shipment import PurolatorShipment
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException, RateException
from api.globals.carriers import PUROLATOR
from brain.settings import PURO_BASE_URL


class PurolatorShip(PurolatorBaseApi):
    """
    Purolator Ship Class
    """

    _version = "2.2"
    _service = None

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._puro_shipment = PurolatorShipment(
            is_rate=False, ubbe_request=self._ubbe_request
        )
        self._puro_rate = PurolatorRate(ubbe_request=ubbe_request)
        self._pure_doc = PurolatorDocument(ubbe_request=ubbe_request)

        self._order_number = self._ubbe_request["order_number"]
        self._service_code = self._ubbe_request["service_code"]

        self.create_connection(wsdl_path="ShippingService.wsdl", version=self._version)
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v2}ShippingServiceEndpointV2",
            f"{PURO_BASE_URL}/EWS/v2/Shipping/ShippingService.asmx",
        )

        self._response = {}

    def _format_response(self, response: dict) -> None:
        """
        Format puro response into ubbe api response. Also get the cost, documents, and create a pickup.
        :param response: Puro response
        :return:
        """
        pin = response["ShipmentPIN"]["Value"]

        puro_rate = self._puro_rate.get_rate(is_all_rate=False)

        if not puro_rate:
            raise ShipException({"api.error.purolator.ship": "Get rate failed:."})

        rate = self._puro_rate.format_response_single(rates=puro_rate)

        try:
            documents = self._pure_doc.documents(pin=pin)
        except RateException as e:
            raise ShipException(
                {"api.error.purolator.ship": f"Document Failure: {e.message}."}
            ) from e

        self._response = {
            "total": rate["total"],
            "freight": rate["freight"],
            "taxes": rate["tax"],
            "surcharges": rate["surcharges"],
            "surcharges_cost": rate["surcharge"],
            "tax_percent": rate["tax_percent"],
            "carrier_id": PUROLATOR,
            "service_code": self._service_code,
            "carrier_name": self._courier_name,
            "service_name": self._puro_service.get(
                self._service_code, self._courier_name
            ),
            "transit_days": rate["transit_days"],
            "delivery_date": rate["delivery_date"],
            "tracking_number": pin,
            "documents": documents,
            "pickup_id": "",
        }

    def _ship_post(self, request: dict) -> dict:
        """
        Send Create Shipment request to purolator.
        :return:
        """

        try:
            response = self._service.CreateShipment(
                _soapheaders=[
                    self._build_request_context(
                        reference=f"CreateShipment - {self._order_number}",
                        version=self._version,
                    )
                ],
                Shipment=request,
                PrinterType="Thermal",
            )
        except (Fault, ValueError) as e:
            error = f"CreateShipment Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_ship.py line: 114",
                message=str({"api.error.purolator.ship": f"{error}"}),
            )
            raise ShipException(
                {"api.error.purolator.ship": f"Shipping Failure: {str(e)}."}
            ) from e

        return response["body"]

    def _validate_post(self, shipment: dict) -> bool:
        """
        Send Void Shipment request to purolator.
        :return:
        """

        try:
            response = self._service.ValidateShipment(
                _soapheaders=[
                    self._build_request_context(
                        reference=f"ValidShipment - {self._order_number}",
                        version=self._version,
                    )
                ],
                Shipment=shipment,
            )
        except (Fault, ValueError) as e:
            error = f"ValidShipment Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_ship.py line: 137",
                message=str({"api.error.purolator.ship": f"{error}"}),
            )
            raise ShipException(
                {"api.error.purolator.void": f"Void Failure: {str(e)}."}
            ) from e

        if "ValidShipment" in response["body"]:
            is_validate = response["body"]["ValidShipment"]
        else:
            is_validate = False

        return is_validate

    def _void_post(self, pin: str) -> None:
        """
        Send Void Shipment request to purolator.
        :return:
        """

        try:
            response = self._service.VoidShipment(
                _soapheaders=[
                    self._build_request_context(
                        reference=f"VoidShipment - {pin}", version=self._version
                    )
                ],
                PIN=pin,
            )
        except (Fault, ValueError) as e:
            error = f"VoidShipment Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_ship.py line: 165",
                message=str({"api.error.purolator.ship": f"{error}"}),
            )
            raise ShipException(
                {"api.error.purolator.void": f"Void Failure: {str(e)}."}
            ) from e

        if "ShipmentVoided" in response["body"]:
            is_void = response["body"]["ShipmentVoided"]
        else:
            is_void = False

        if not is_void:
            code = response["body"]["ResponseInformation"]["Errors"]["Error"][0]["Code"]
            message = response["body"]["ResponseInformation"]["Errors"]["Error"][0][
                "Description"
            ]
        else:
            code = ""
            message = ""

        self._response = {"is_void": is_void, "message": f"{code} - {message}"}

    def ship(self) -> dict:
        """
        Ship Purolator shipment.
        :return:
        """

        try:
            request = self._puro_shipment.shipment(account_number=self._account_number)
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_ship.py line: 194",
                message=f"Purolator Ship: {str(e)}, Data: {str(e)}",
            )
            connection.close()
            raise ShipException(
                {
                    "api.error.purolator.ship": "Ship Request Fail: Please contact support."
                }
            ) from e

        try:
            is_valid = self._validate_post(shipment=request)
        except (ShipException, KeyError) as e:
            CeleryLogger().l_critical.delay(
                location="purolator_ship.py line: 204",
                message=f"Purolator Ship: {str(e)}, Data: {str(request)}",
            )
            connection.close()
            raise ShipException(
                {
                    "api.error.purolator.ship": "Shipping Failure: Please contact support."
                }
            ) from e

        if not is_valid:
            connection.close()
            raise ShipException(
                {"api.error.purolator.ship": "Shipping Failure: Shipment not valid."}
            )

        try:
            response = self._ship_post(request=request)
        except (ShipException, KeyError) as e:
            CeleryLogger().l_critical.delay(
                location="purolator_ship.py line: 218",
                message=f"Purolator Ship: {str(e)}, Data: {str(request)}",
            )
            connection.close()
            raise ShipException(
                {
                    "api.error.purolator.ship": "Shipping Failure: Please contact support."
                }
            ) from e

        try:
            self._format_response(response=response)
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_ship.py line: 228",
                message=f"Purolator Ship: {str(e)}, Data: {str('')}",
            )
            connection.close()
            raise ShipException(
                {
                    "api.error.purolator.ship": "Ship Format Error: Please contact support.}"
                }
            ) from e

        connection.close()
        return self._response

    def void(self, pin: str) -> dict:
        """
        Void Purolator shipment.
        :return:
        """

        try:
            self._void_post(pin=pin)
        except (ShipException, KeyError) as e:
            CeleryLogger().l_critical.delay(
                location="purolator_ship.py line: 251",
                message=f"Purolator Ship: {str(e)}, Data: {str('')}",
            )
            # connection.close()
            raise ShipException(
                {"api.error.purolator.void": "Void Failure: Please contact support."}
            ) from e

        # connection.close()
        return self._response
