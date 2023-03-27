"""
    Title: Calm Air Ship Class
    Description: This file will contain functions related to Calm Air Ship Apis.
    Created: August 20, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from datetime import date
from decimal import Decimal

import lxml
import requests
from django.core.cache import cache
from django.db import connection
from lxml import etree

from api.apis.carriers.calm_air.endpoints.calm_air_base import CalmAirBase
from api.background_tasks.logger import CeleryLogger
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import ShipException, RequestError
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING, DEFAULT_TIMEOUT_SECONDS,
)
from api.utilities.date_utility import DateUtility


class CalmAirShip(CalmAirBase):
    """
    Class will handle all details about a Calm Air Ship request and return appropriate data.

    Units: Metric Units are used for this api
    """

    _ship_end = "/export/createwaybill"

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._order_number = ubbe_request["order_number"]
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._service_code = self._ubbe_request["service_code"]
        self._url = self._base_url + self._ship_end

        self._request = None
        self._request_response = None
        self._response = {}

    def _build(self) -> None:
        """
        Build params for ship request.
        :return: None
        """
        po_number = (
            f'{self._order_number}/{self._ubbe_request.get("reference_one", "")}'
        )
        service_code_parts = self._service_code.split("-")

        special_instructions = self._ubbe_request.get("special_instructions", "")[:20]

        if special_instructions == "":
            special_instructions = "NULL"

        self._request = {
            "user_name": self._login,
            "customer_account_number": self._account_number,
            "access_key": self._key,
            "rate_code": service_code_parts[0],
            "origin_airport": self._origin["base"],
            "dest_airport": self._destination["base"],
            "currency_code": "CAD",
            "declared_value": self._zero,
            "po_number": self._order_number[:20],
            "remarks": special_instructions,
            "awb_no": "NULL",
        }

        packages = self._build_packages()
        self._request.update(packages)

        self._build_address(key_type="shipper", address=self._origin)
        self._build_contact(key_type="shp", contact=self._origin)
        self._build_address(key_type="consignee", address=self._destination)
        self._build_contact(key_type="con", contact=self._destination)

    def _build_address(self, key_type: str, address) -> None:
        """
        Build address details, with passed in keys and data
        :param key_type: param key
        :param address: address dictionary
        :return:
        """

        self._request.update(
            {
                f"{key_type}_name": address["name"][:20],
                f"{key_type}_acc": self._account_number,
                f"{key_type}_tel": address["phone"],
                f"{key_type}_mobile": address["phone"],
                f"{key_type}_email": "customerservice@ubbe.com",
            }
        )

    def _build_contact(self, key_type: str, contact) -> None:
        """
        Build contact details, with passed in keys and data
        :param key_type: param key
        :param contact: address dictionary
        :return:
        """

        self._request.update(
            {
                f"{key_type}_str": contact["address"][:20],
                f"{key_type}_plc": contact["city"][:20],
                f"{key_type}_prv": contact["province"],
                f"{key_type}_cnt": contact["country"],
            }
        )

    def _format_response(self) -> None:
        """
        Formant Calm Air ship response into ubbe json response.
        :return:
        """
        zero = Decimal("0").quantize(Decimal(".01"))
        response_details = self._request_response[0]
        airway_bill = str(response_details[0].text)
        label_url = str(response_details[1].text)

        service_code_parts = self._service_code.split("-")
        # Attempt to get cache rate quote
        cached_rate = cache.get(self._service_code)

        try:
            if not cached_rate:
                cached_rate = {}
                service_name = "General"
            else:
                cache.delete(self._service_code)
                service_name = cached_rate.get("service_name", "General")
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 132",
                message=f"Calm Air Rate Cache issue: {str(e)}",
            )
            cached_rate = {}
            service_name = "General"

        documents = self._get_documents(
            airway_bill=airway_bill, service_name=service_name, label_url=label_url
        )

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request.get("pickup", {})
        ).get_estimated_delivery(
            transit=self._services_transit.get("service_code", 4),
            country=self._ubbe_request["origin"]["country"],
            province=self._ubbe_request["origin"]["province"],
        )

        self._response = {
            "freight": cached_rate.get("freight", zero),
            "surcharges": [],
            "taxes": cached_rate.get("tax", zero),
            "tax_percent": cached_rate.get("tax_percent", zero),
            "total": cached_rate.get("total", zero),
            "surcharges_cost": cached_rate.get("surcharge", zero),
            "carrier_id": self._carrier_id,
            "carrier_name": self._carrier_name,
            "service_code": service_code_parts[0],
            "service_name": service_name,
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
            "tracking_number": airway_bill,
            "documents": documents,
        }

    def _get_documents(
        self, airway_bill: str, service_name: str, label_url: str = ""
    ) -> list:
        """
        Generate Documents for request
        :return: Return list of dictionary documents
        """
        service_code_parts = self._service_code.split("-")
        airway_bill_parts = airway_bill.split("-")

        self._ubbe_request["carrier"] = self._ubbe_request["carrier_name"]
        self._ubbe_request["is_carrier_metric"] = self._carrier.is_kilogram
        self._ubbe_request["order_date"] = date.today().strftime("%Y/%m/%d")
        self._ubbe_request["calm_air_format"] = date.today().strftime("%d %b %Y")
        self._ubbe_request["request_date"] = self._ubbe_request["order_date"]
        self._ubbe_request["carrier_account"] = self._account_number
        self._ubbe_request["service_name"] = service_name
        self._ubbe_request["service"] = service_name
        self._ubbe_request["service_code"] = service_code_parts[0]
        self._ubbe_request[
            "bol"
        ] = f'{airway_bill_parts[0]}-{self._origin["base"]}-{airway_bill_parts[1]}'
        self._ubbe_request[
            "bol_number"
        ] = f'{airway_bill_parts[0]}-{self._origin["base"]}-{airway_bill_parts[1]}'
        self._ubbe_request[
            "awb"
        ] = f'{airway_bill_parts[0]}-{self._origin["base"]}-{airway_bill_parts[1]}'
        statement = (
            f'Booked on {self._ubbe_request["carrier_name"]} AWB {airway_bill}.\n'
        )
        self._ubbe_request["handling_notes"] = statement + self._ubbe_request.get(
            "special_instructions", ""
        )

        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)

        if label_url:
            label = manual_docs.generate_calm_air_label()
        else:
            label = manual_docs.generate_calm_air_label()

        return [
            {"document": label, "type": DOCUMENT_TYPE_SHIPPING_LABEL},
            {
                "document": manual_docs.generate_airwaybill(
                    carrier_id=self._carrier_id
                ),
                "type": DOCUMENT_TYPE_BILL_OF_LADING,
            },
        ]

    def _post(self) -> None:
        """
        Make Calm Air ship call
        """

        temp = "<NewDataSet><DefaultView><AirWaybill>622-22096432</AirWaybill><Print_Label>https://cargo.calmair.com/common/print_label?public=1&amp;bill_no=622-22096432</Print_Label><Print_Waybill>https://cargo.calmair.com/common/print_awb?bill_no=622-22096432</Print_Waybill></DefaultView></NewDataSet>"

        try:
            response = requests.get(self._url, params=self._request, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 117",
                message=f"Calm Air Rate posting data: {self._request}"
            )
            raise RequestError(None, self._request) from e

        if not response.ok:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 125",
                message=f"Calm Air posting data: {self._request} \nCalm Air return data: {response.text}"
            )
            raise RequestError(response, self._request)

        # TODO - Add try and except

        try:
            self._request_response = etree.fromstring(response.text)
            # self._request_response = etree.fromstring(temp)
        except lxml.etree.XMLSyntaxError as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 125",
                message=f"Calm Air data: {self._request} \nCalm Air return data: {response.text}"
            )
            raise RequestError(response, self._request) from e

        if self._request_response[0][0].tag == "ERRORMESSAGE":
            connection.close()
            CeleryLogger().l_critical.delay(
                location="calm_air_rate.py line: 125",
                message=f"Calm Air data: {self._request} \nCalm Air return data: {response.text}"
            )
            raise RequestError(response, self._request)
            # raise ShipException({"api.ship.error": "CalmAir: API not active"})

    def ship(self, order_number="") -> dict:
        """
        Create ship & validate request to the carrier endpoint.
        :return:
        """

        # Build request
        try:
            self._build()
        except ShipException as e:
            connection.close()
            raise ShipException(
                code="29201", message=f"CalmAir API (L250): {e.message}", errors=[]
            ) from e

        # Send request
        try:
            self._post()
        except RequestError as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_ship.py line: 257", message=f"Calm Air: {str(e)}"
            )
            raise ShipException(
                code="29202", message=f"CalmAir API (L244): {str(e)}", errors=[]
            ) from e
        except lxml.etree.XMLSyntaxError as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="calm_air_ship.py line: 257", message=f"Calm Air: {str(e)}"
            )
            raise ShipException(
                code="29203", message=f"CalmAir API (L244): {str(e)}", errors=[]
            ) from e

        try:
            self._format_response()
        except ShipException as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_ship.py line: 213", message=f"Calm Air: {e.message}"
            )
            connection.close()
            raise ShipException(
                code="29204", message=f"CalmAir API (L267): {e.message}", errors=[]
            ) from e

        connection.close()
        return self._response
