"""
    Title: ABF Freight Document Api
    Description: This file will contain functions related to ABF Document Apis.
    Created: June 28, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from typing import Union

import requests
import xmltodict
from django.db import connection

from api.exceptions.project import RequestError, DocumentException
from api.globals.project import DEFAULT_TIMEOUT_SECONDS


class ABFDocument:
    """
    ABF Document Class
    """

    _url = "https://www.abfs.com/xml/docretxml.asp"

    _abf_document_types = [
        "BOL",
        "DR",
        "INV",
        "PSL",
        "WSL",
        "WRP",
        "WINS",
        "CUS",
        "CBL",
        "CON",
        "RECO",
        "Str",
        "EQAD",
        "BOND",
        "RDR",
        "FFWD",
        "DIM",
        "AFSS",
    ]

    _abf_ubbe_map = {
        "BOL": "0",
        "DR": "2",
        "INV": "4",
        "PSL": "1",
        "WSL": "4",
        "WRP": "99",
        "WINS": "99",
        "CUS": "99",
        "CBL": "99",
        "CON": "99",
        "RECO": "99",
        "Str": "99",
        "EQAD": "99",
        "BOND": "99",
        "RDR": "99",
        "FFWD": "99",
        "DIM": "99",
        "AFSS": "99",
    }

    _ubbe_pod = 8
    _ubbe_weight_inspection = 9
    _document_types = [("D", _ubbe_pod), ("W", _ubbe_weight_inspection)]

    @staticmethod
    def _get_documents_requests(tracking_number: str, document_types: list) -> list:
        """
        Get POD and Weight inspections for yrc shipment
        :return: list of documents.
        """
        document_requests = []

        for document_type in document_types:
            document_requests.append(
                {
                    "ID": tracking_number,
                    "RefNum": tracking_number,
                    "RefType": "A",
                    "DocType": document_type,
                    "ImageType": "L",
                }
            )

        return document_requests

    def _check_document_types(self, document_types: list):
        """
        Check document types for request.
        :param document_types:
        :return:
        """

        if not document_types:
            raise DocumentException("ABF Document (L113): Empty Document Types")

        for doc in document_types:
            if doc not in self._abf_document_types:
                raise DocumentException("ABF Document (L113): Invalid Document Types")

    def _get(self, params: dict = None, headers: dict = None) -> Union[list, dict]:
        """
        Make ABF Freight get api call.
        """

        if not params:
            params = {}

        try:
            response = requests.get(
                url=self._url,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                headers=headers,
                params=params,
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": self._url, "error": str(e)}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": self._url})

        try:
            converted_xml = xmltodict.parse(xml_input=response.content)
        except KeyError as e:
            raise RequestError(response, {"url": self._url, "error": str(e)}) from e

        return converted_xml

    def _format_response(self, request: dict, response: dict) -> dict:
        """
        Format documents into ubbe format to be saved.
        :return:
        """

        ret = {
            "shipment_id": "",
            "document": "",
            "doc_type": self._abf_ubbe_map[request["DocType"]],
        }

        return ret

    def _get_documents(self, document_requests: list) -> list:
        """
        Get documents for yrc shipment.
        :param tracking_number:
        :param document_types:
        :return:
        """
        responses = []

        for request in document_requests:
            try:
                document = self._get(params=request)
            except RequestError as e:
                connection.close()
                raise DocumentException(f"ABF Ship (L292): {str(e)}") from e

            responses.append(document)

        return responses

    def document(self, tracking_number: str, document_types: list) -> list:
        """
        Get documents for yrc shipment.
        :param tracking_number:
        :param document_types:
        :return:
        """

        if not tracking_number:
            raise DocumentException(
                "ABF Document (L113): No Tracking ID Tracking or Pickup Date."
            )

        self._check_document_types(document_types=document_types)

        document_requests = self._get_documents_requests(
            tracking_number=tracking_number, document_types=document_types
        )

        if not document_requests:
            raise DocumentException(
                "ABF Document (L113): No Tracking ID Tracking or Pickup Date."
            )

        try:
            documents = self._get_documents(document_requests=document_requests)
        except Exception as e:
            raise DocumentException(
                "ABF Document (L113): No Tracking ID Tracking or Pickup Date."
            ) from e

        return documents
