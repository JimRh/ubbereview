"""
    Title: YRC Document Api
    Description: This file will contain functions related to YRC Document Apis.
    Created: January 20, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64

import requests
from django.db import connection

from api.exceptions.project import RequestError, TrackException, DocumentException
from api.globals.project import DEFAULT_TIMEOUT_SECONDS


class YRCDocument:
    """
    YRC Document Class
    """

    _url = "http://my.yrc.com/myyrc-api/national/servlet"

    _ubbe_pod = "2"
    _ubbe_weight_inspection = "4"
    _document_types = [("D", _ubbe_pod), ("W", _ubbe_weight_inspection)]

    def _get(self, data: dict):
        """
        Make YRC document call.
        """

        try:
            response = requests.get(
                url=self._url, params=data, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(
                None, {"url": self._url, "error": str(e), "data": data}
            ) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": self._url, "data": data})

        if response.headers["Content-Type"] == "text/xml":
            raise DocumentException(
                f'YRC Document (L50): No document for {data["docType"]}.'
            )

        try:
            yrc_ret = response.content
        except ValueError as e:
            connection.close()
            raise RequestError(
                response, {"url": self._url, "error": str(e), "data": data}
            ) from e

        connection.close()
        return yrc_ret

    def _get_documents(self, params: dict) -> list:
        """
        Get POD and Weight inspections for yrc shipment
        :return: list of documents.
        """
        documents = []

        for document_type, ubbe_type in self._document_types:
            params["docType"] = document_type

            try:
                response = self._get(data=params)
            except DocumentException:
                continue

            encoded = base64.b64encode(response)

            documents.append({"document": encoded.decode("ascii"), "type": ubbe_type})

        return documents

    def document(self, tracking_number: str, pickup_date: str) -> list:
        """
        Get documents for yrc shipment.
        :param tracking_number:
        :param pickup_date:
        :return:
        """

        if not tracking_number:
            raise TrackException(
                "YRC Document (L113): No Tracking ID Tracking or Pickup Date."
            )

        params = {
            "CONTROLLER": "com.rdwy.ec.rexpublicdocumentsapi.http.controller.PublicDocAPIController",
            "refNumber": tracking_number,
            "refNumberType": "PR",
            "pickupDate": pickup_date,
            "requestType": "S",
        }

        documents = self._get_documents(params=params)

        return documents
