"""
    Title: Action Express Document Api
    Description: This file will contain functions related to Action Express Document Apis.
    Created: June 9, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64

import requests
from django.db import connection

from api.apis.carriers.action_express.endpoints.ac_api import ActionExpressApi
from api.exceptions.project import ShipException, RequestError
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
    DEFAULT_TIMEOUT_SECONDS,
)


class ActionExpressDocument(ActionExpressApi):
    """
    Action Express Document Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    def _process_document(self, document_type: str, response) -> dict:
        """
        Process Action Express tracking response for the latest status and format into ubbe shipment tracking
        status.
        :return: dict of latest tracking status
        """

        if document_type == self._LABEL:
            d_type = DOCUMENT_TYPE_SHIPPING_LABEL
        else:
            d_type = DOCUMENT_TYPE_BILL_OF_LADING

        encoded = base64.b64encode(response)

        return {"document": encoded.decode("UTF-8"), "type": d_type}

    def _get_document(self, url: str, params: dict = None, headers: dict = None):
        """
        Make Action Express api call.
        """

        if not params:
            params = {}

        if not headers:
            headers = {}

        headers.update(self._auth)

        try:
            response = requests.get(
                url=url, timeout=DEFAULT_TIMEOUT_SECONDS, headers=headers, params=params
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": url, "error": str(e)}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": url})

        connection.close()
        return response.content

    def _get_documents(self, order_id: str) -> list:
        """
        Get documents such as BOL and Cargo labels for the action express shipment.
        :return: list of dicts
        """
        documents = []
        headers = {"Accept": "application/pdf"}

        for document in self._document_types:
            doc_response = self._get_document(
                url=f"{self._url}/order/report",
                params={"type": document, "id": order_id},
                headers=headers,
            )
            documents.append(
                self._process_document(document_type=document, response=doc_response)
            )

        return documents

    def documents(self, order_id: str) -> list:
        """
        Get all required documents such as BOL and Cargo labels for Action Express shipment.
        :param order_id: Action Express Order ID Number.
        :return: list of dicts in base64 format
        """

        if not order_id:
            connection.close()
            raise ShipException(
                code="27204", message="AE Document (L67): Invalid Order ID.", errors=[]
            )

        try:
            documents = self._get_documents(order_id=order_id)
        except Exception as e:
            connection.close()
            raise ShipException(
                code="27205", message=f"AE Document (L73): {str(e)}", errors=[]
            ) from e

        connection.close()
        return documents
