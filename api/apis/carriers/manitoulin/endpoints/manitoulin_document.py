"""
    Title: Manitoulin Document Api
    Description: This file will contain functions related to Manitoulin Document Apis.
    Created: January 4, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi
from api.exceptions.project import (
    RequestError,
    ViewException,
)
from api.globals.project import (
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_SHIPPING_LABEL,
)


class ManitoulinDocument(ManitoulinBaseApi):
    """
    Manitoulin Document Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    @staticmethod
    def _build_shipping_documents(bol_id: int) -> tuple:
        """
        Builds request for getting shipping documents
        :param bol_id:
        :return: bol pdf, bol label
        """

        bol = {"bol_ids": [bol_id]}

        label = {"bol": bol_id}

        return bol, label

    def get_documents(self, bol_id: int) -> list:
        """
        Get BOL and Shipping Label for shipment
        :params: bol id
        :return: list of documents
        """
        documents = []

        bol, label = self._build_shipping_documents(bol_id=bol_id)

        for url, request, doc_type in [
            (self._bol_pdf, bol, DOCUMENT_TYPE_BILL_OF_LADING),
            (self._bol_labels, label, DOCUMENT_TYPE_SHIPPING_LABEL),
        ]:
            try:
                response = self._post(url=url, request=request)
            except RequestError as e:
                connection.close()
                raise ViewException(f"Manitoulin Ship (L373): {str(e)}") from e

            if doc_type == DOCUMENT_TYPE_BILL_OF_LADING:
                doc_ret = response[0]
                document = doc_ret["pdf"][0]
            else:
                document = response[0]

            documents.append({"document": document, "type": doc_type})

        connection.close()
        return documents

    def get_tracking_documents(self, tracking_number: str) -> list:
        pass
