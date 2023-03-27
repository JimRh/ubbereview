"""
    Title: Cargojet Document Api
    Description: This file will contain functions related to Cargojet Document Apis.
    Created: Sept 27, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.carriers.cargojet.endpoints.cj_api import CargojetApi
from api.documents.commercial_invoice import CommercialInvoice
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import ShipException
from api.globals.carriers import CARGO_JET
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)


class CargojetDocument(CargojetApi):
    """
    Cargojet Document Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _get_documents(self) -> list:
        """
        Generate Documents: BOL, Cargo Labels. If needed: CI.
        :return: list of pdfs
        """
        self._ubbe_request["carrier"] = self._carrier_name
        self._ubbe_request["carrier_name"] = self._carrier_name
        self._ubbe_request["service"] = self._normal_service
        self._ubbe_request["service_name"] = self._normal_service
        self._ubbe_request[
            "carrier_account"
        ] = self._carrier_account.account_number.decrypt()

        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)

        documents = [
            {
                "document": manual_docs.generate_airwaybill(carrier_id=CARGO_JET),
                "type": DOCUMENT_TYPE_BILL_OF_LADING,
            },
            {
                "document": manual_docs.generate_cargo_label(),
                "type": DOCUMENT_TYPE_SHIPPING_LABEL,
            },
        ]

        if self._ubbe_request.get("is_dangerous_shipment", False):
            documents.append(self._dg_service.generate_documents())

        if self._ubbe_request["is_international"]:
            invoice = CommercialInvoice(
                shipdata=self._ubbe_request,
                order_number=self._ubbe_request["order_number"],
            ).get_pdf()
            documents.append(
                {"document": invoice, "type": DOCUMENT_TYPE_COMMERCIAL_INVOICE}
            )

        return documents

    def documents(self) -> list:
        """
        Get all required documents such as BOL and Cargo labels for Cargojet shipment.
        :return: list of dicts in base64 format
        """

        try:
            documents = self._get_documents()
        except Exception as e:
            connection.close()
            raise ShipException(f"CJ Document (L73): {str(e)}") from e

        connection.close()
        return documents
