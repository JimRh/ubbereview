"""
    Title: TST CF Express Rate api
    Description: This file will contain functions related to TST CF Express rate Api.
    Created: January 20, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection
from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_base_v2 import TstCfExpressApi
from api.exceptions.project import RequestError, ViewException


class TstCfExpressDocument(TstCfExpressApi):
    """
    TST CF Express Ship Class

    Units: Imperial Units are used for this api
    """

    _document_types = ["POD"]
    _ubbe_pod = "2"

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._leg = self._ubbe_request["leg"]
        self._tracking_number = self._ubbe_request["tracking_number"]

        self._request = []
        self._response = {}

    def _build(self, document_type: str) -> etree.Element:
        """
        Build document request for tst pod.
        :return: TST request
        """

        request = etree.Element("imagerequest")

        # Only add for testing.
        if self._is_test:
            request.append(self._add_child(element="testmode", value="Y"))

        self._add_auth(request=request)
        request.append(self._add_child(element="type", value=document_type))
        request.append(self._add_child(element="pro", value=self._tracking_number))

        return request

    def document(self) -> list:
        """
        Get documents for tst shipment.
        :return:
        """
        documents = []

        for document in self._document_types:
            request = self._build(document_type=document)

            try:
                response = self._post(
                    url=self._image_url, return_key="imageresults", request=request
                )
            except RequestError as e:
                connection.close()
                raise ViewException(
                    f"TST-CF Document (L187): Failed Post. {str(e)}"
                ) from e

            documents.append(
                {"document": response["images"][0]["imagedata"], "type": self._ubbe_pod}
            )

        return documents
