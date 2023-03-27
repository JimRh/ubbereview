"""
    Title: TST CF Express Rate api
    Description: This file will contain functions related to TST CF Express rate Api.
    Created: January 10, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from datetime import date

from django.core.cache import cache
from django.db import connection
from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_base_v2 import TstCfExpressApi
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_rate_v2 import TstCfExpressRate
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import RateException, RequestError, ShipException
from api.globals.carriers import TST
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
)
from api.models import CityNameAlias


class TstCfExpressBOL(TstCfExpressApi):
    """
    TST CF Express Ship Class

    Units: Imperial Units are used for this api
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._lookup = copy.deepcopy(self._ubbe_request["service_code"])
        service_code, quote_id = self._ubbe_request["service_code"].split("-")
        self._service_code = service_code
        self._quote_id = quote_id

        self._origin = self._ubbe_request.get("origin", {})
        self._destination = self._ubbe_request.get("destination", {})

        self._request = []
        self._response = {}

    def _build(self):
        """
        Build request lxml object for bol request.
        :return: None
        """
        self._request = etree.Element("prorequest")

        if self._is_test:
            self._request.append(self._add_child(element="mode", value="T"))

        # Add Auth to request
        self._add_auth(request=self._request)

        city = CityNameAlias.check_alias(
            self._origin["city"], self._origin["province"], self._origin["country"], TST
        )

        self._request.append(
            self._add_child(element="zip", value=self._origin["postal_code"])
        )
        self._request.append(self._add_child(element="city", value=city.upper()))
        self._request.append(
            self._add_child(element="state", value=self._origin["province"])
        )

    def _generate_documents(self, pro: str) -> list:
        """
        Generate Documents for request
        :param pro: Tracking Number
        :return: Return list of dictionary documents
        """

        self._ubbe_request["carrier"] = self._carrier_name
        self._ubbe_request["service"] = self._services_names[self._service_code]
        self._ubbe_request["service_name"] = self._services_names[self._service_code]
        self._ubbe_request["bol_number"] = pro
        self._ubbe_request["bol"] = pro
        self._ubbe_request["request_date"] = date.today().strftime("%Y/%m/%d")

        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)

        return [
            {
                "document": manual_docs.generate_cargo_label(),
                "type": DOCUMENT_TYPE_SHIPPING_LABEL,
            },
            {
                "document": manual_docs.generate_bol(),
                "type": DOCUMENT_TYPE_BILL_OF_LADING,
            },
        ]

    def _format_rate(self) -> None:
        """

        :return:
        """

        # Attempt to get cache rate quote
        cached_rate_data = cache.get(self._lookup)

        if not cached_rate_data:
            # TODO - Think about this
            tst_rate = TstCfExpressRate(ubbe_request=self._ubbe_request)
            return tst_rate.get_rate_cost(service=self._service_code)

        ubbe_response = cached_rate_data["ubbe"]

        self._response.update(
            {
                "freight": ubbe_response["freight"],
                "surcharges": ubbe_response["surcharge_list"],
                "taxes": ubbe_response["tax"],
                "tax_percent": ubbe_response["tax_percent"],
                "total": ubbe_response["total"],
                "surcharges_cost": ubbe_response["surcharge"],
                "transit_days": ubbe_response["transit_days"],
                "delivery_date": ubbe_response["delivery_date"],
            }
        )

    def _format_response(self, response: dict):
        """

        :param response:
        :return:
        """

        pro_number = str(response.get("pro", ""))

        documents = self._generate_documents(pro=pro_number)

        self._response.update(
            {
                "carrier_id": self._carrier_id,
                "carrier_name": self._carrier_name,
                "service_code": self._service_code,
                "service_name": self._services_names[self._service_code],
                "tracking_number": pro_number,
                "carrier_api_id": self._quote_id,
                "documents": documents,
            }
        )
        self._format_rate()

    def ship(self) -> dict:
        """
        Get rates for TST Overland
        :return: list of dictionary rates
        """

        if (
            self._origin["province"] in self._north
            or self._destination["province"] in self._north
        ):
            connection.close()
            raise ShipException("TST-CF Ship (L187): Not Supported Region.")

        try:
            self._build()
        except RateException as e:
            connection.close()
            raise ShipException(
                f"2Ship Rate (L198): Failed building request. {e.message}"
            ) from e

        try:
            response = self._post(
                url=self._bol_url, return_key="proresults", request=self._request
            )
        except RequestError as e:
            connection.close()
            raise ShipException(f"TST-CF Rate (L187): Failed Post. {str(e)}") from e

        try:
            self._format_response(response=response)
        except KeyError as e:
            connection.close()
            raise ShipException(f"2Ship Ship (L367): {str(e)}") from e

        return self._response
