"""
    Title: BBE Ship Api
    Description: This file will contain functions related to BBE ship Api.
    Created: July 13, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from datetime import date

import gevent
from django.db import connection

from api.apis.carriers.bbe.endpoints.bbe_api_v1 import BBEAPI
from api.apis.services.taxes.taxes import Taxes
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import ShipException, RequestError
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
)
from api.models import RateSheet
from api.utilities.date_utility import DateUtility


class BBEShip(BBEAPI):
    """
    Class will handle all details about a BBE Ship requests.
    """

    def __init__(self, ubbe_request: dict):
        super().__init__(ubbe_request)
        self._response = {}
        self._order_number = ubbe_request["order_number"]
        self._service_code = ubbe_request["service_code"]

    def _get_documents(self, sheet: RateSheet):
        """
        Generate shipping documents for the shipment.
        :param sheet:
        :return:
        """

        # add additional fields for the documents
        self._ubbe_request["carrier"] = sheet.carrier.name
        self._ubbe_request["service"] = sheet.service_name
        self._ubbe_request["order_number"] = self._order_number
        self._ubbe_request["bol"] = self._order_number
        self._ubbe_request["request_date"] = date.today().strftime("%Y/%m/%d")
        self._ubbe_request["order_date"] = date.today().strftime("%Y/%m/%d")

        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)

        # Create threads for BOL and Cargo labels
        bol_thread = gevent.Greenlet.spawn(manual_docs.generate_bol)
        piece_label_thread = gevent.Greenlet.spawn(manual_docs.generate_cargo_label)
        threads = [bol_thread, piece_label_thread]

        # Check for DG shipment, if yes add to threads
        if self._ubbe_request.get("is_dg_shipment", False):
            dg_ground = self._ubbe_request["dg_service"]
            dg_thread = gevent.Greenlet.spawn(dg_ground.generate_documents())
            threads.append(dg_thread)

        # join threads
        gevent.joinall(threads)

        # Get the documents
        piece_label = piece_label_thread.value
        bol = bol_thread.value

        documents = [
            {"document": piece_label, "type": DOCUMENT_TYPE_SHIPPING_LABEL},
            {"document": bol, "type": DOCUMENT_TYPE_BILL_OF_LADING},
        ]

        # Check for DG shipment, if yes, get the document
        if self._ubbe_request.get("is_dg_shipment", False):
            documents.append(dg_thread.value)

        return documents

    def _process_cost(self):
        """
        Get shipment cost for a given lane.
        :return: None
        """

        surcharge_cost = self._zero
        surcharges = []

        sheet = self.get_rate_sheet_ship()

        if not sheet:
            raise ShipException(
                code="32200",
                message="BBE API: Rate could not be determined: No Lanes",
                errors=[],
            )

        self._ubbe_request["carrier_email"] = sheet.carrier.email

        if sheet.is_metric:
            weight = self._ubbe_request["total_weight"]
        else:
            weight = self._ubbe_request["total_weight_imperial"]

        # Get Freight Cost
        try:
            freight_cost = self._get_freight_cost(sheet, weight).quantize(self._sig_fig)
        except ShipException as e:
            connection.close()
            raise ShipException(
                code="32201",
                message="BBE API: The freight cost could not determined.",
                errors=[],
            ) from e

        # Get Fuel Surcharge Cost
        fuel_surcharge = self._get_fuel_surcharge_cost(
            final_weight=weight, freight_cost=freight_cost
        )
        surcharge_cost += fuel_surcharge["cost"]
        surcharges.append(fuel_surcharge)

        # Taxes
        try:
            taxes = Taxes(self._destination).get_tax_rate(freight_cost + surcharge_cost)
        except RequestError as e:
            connection.close()
            raise ShipException(
                code="32202", message="BBE API: Error fetching tax", errors=[]
            ) from e

        # Generate Documents
        documents = self._get_documents(sheet=sheet)

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request.get("pickup")
        ).get_estimated_delivery(
            transit=sheet.transit_days,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        self._response = {
            "api_pickup_id": "",
            "carrier_id": sheet.carrier.code,
            "carrier_name": sheet.carrier.name,
            "documents": documents,
            "freight": freight_cost,
            "carrier_pickup_id": "",
            "service_code": sheet.service_code,
            "service_name": sheet.service_name,
            "surcharges": surcharges,
            "surcharges_cost": surcharge_cost,
            "taxes": taxes,
            "tax_percent": (
                (taxes / (freight_cost + surcharge_cost)) * self._hundred
            ).quantize(self._sig_fig),
            "total": freight_cost + surcharge_cost + taxes,
            "tracking_number": self._order_number,
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
        }

    def _process_quote(self):
        self._response = {
            "api_pickup_id": "",
            "carrier_id": self._carrier_id,
            "carrier_name": "BBE",
            "documents": [],
            "freight": self._zero,
            "carrier_pickup_id": "",
            "service_code": self._service_code,
            "service_name": "Quote",
            "surcharges": [],
            "surcharges_cost": self._zero,
            "taxes": self._zero,
            "tax_percent": self._zero,
            "total": self._zero,
            "tracking_number": "",
            "transit_days": -1,
        }

    def ship(self) -> dict:
        """
        Ship the request
        :return: shipment details in Dictionary Form.
        """

        if self._service_code == "BBEQUO":
            self._process_quote()
        else:
            self._process_cost()

        return self._response
