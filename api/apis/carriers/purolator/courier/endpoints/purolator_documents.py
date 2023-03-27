"""
    Title: Purolator Document
    Description: This file will contain functions related to Purolator Document Apis.
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
from api.background_tasks.logger import CeleryLogger
from api.documents.commercial_invoice import CommercialInvoice
from api.exceptions.project import ShipException
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)
from brain.settings import PURO_BASE_URL


class PurolatorDocument(PurolatorBaseApi):
    """
    Purolator Document Class
    """

    _version = "1.4"
    _service = None

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._order_number = self._ubbe_request["order_number"]

        self.create_connection(
            wsdl_path="ShippingDocumentsService.wsdl", version=self._version
        )
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v1}ShippingDocumentsServiceEndpoint",
            f"{PURO_BASE_URL}/EWS/V1/ShippingDocuments/ShippingDocumentsService.asmx",
        )

        self._response = []

    def _add_commercial_invoice(self):
        """
        Add commercial Invoice to document response
        :return:
        """

        self._response.append(
            {
                "document": CommercialInvoice(
                    self._ubbe_request, self._ubbe_request["order_number"]
                ).get_base_64(),
                "type": DOCUMENT_TYPE_COMMERCIAL_INVOICE,
            }
        )

    def _format_response(self, documents: list):
        """
        Format puro document response into ubbe api response.
        :param documents: base64 document.
        :return:
        """

        for document in documents:
            document_details = document["DocumentDetails"]["DocumentDetail"]

            for doc in document_details:
                self._response.append(
                    {"document": doc["Data"], "type": DOCUMENT_TYPE_SHIPPING_LABEL}
                )

    def _post(self, pin: str) -> list:
        """
        Send Get Document request to purolator.
        :return:
        """

        if self._ubbe_request.get("is_international", False):
            doc_type = "InternationalBillOfLadingThermal"
        else:
            doc_type = "DomesticBillOfLadingThermal"

        try:
            response = self._service.GetDocuments(
                _soapheaders=[
                    self._build_request_context(
                        reference=f"GetDocuments - {self._order_number}",
                        version=self._version,
                    )
                ],
                OutputType="PDF",
                Synchronous=True,
                DocumentCriterium={
                    "DocumentCriteria": {
                        "PIN": pin,
                        "DocumentTypes": [{"DocumentType": doc_type}],
                    }
                },
            )
        except (Fault, ValueError) as e:
            error = f"Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_document.py line: 84",
                message=str({"api.error.purolator.document": f"{error}"}),
            )

            return []

        return response["body"]["Documents"]["Document"]

    def documents(self, pin: str) -> list:
        """
        Get Purolator Documents.
        :return:
        """

        try:
            documents = self._post(pin=pin)
        except (ShipException, KeyError) as e:
            error = f"Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_critical.delay(
                location="purolator_document.py line: 119",
                message=f"Purolator Document: {error}, Data: {pin}",
            )
            connection.close()
            raise ShipException(
                {
                    "api.error.purolator.document": "Shipping Failure: Please contact support."
                }
            ) from e

        try:
            self._format_response(documents=documents)
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_document.py line: 136",
                message=f"Purolator Document: {str(e)}, Data: {pin}",
            )
            connection.close()
            raise ShipException(
                {
                    "api.error.purolator.document": "Ship Format Error: Please contact support.}"
                }
            ) from e

        if self._ubbe_request.get("is_international", False):
            self._add_commercial_invoice()

        connection.close()
        return self._response
