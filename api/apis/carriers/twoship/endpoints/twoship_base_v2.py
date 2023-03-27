"""
    Title: TwoShip Api V2
    Description: This file will contain common functionality related to TwoShip Base Api V2.
    Created: Jan 13,, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal
from typing import Union

import requests
from django.db import connection
from rest_framework import status

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, ViewException
from api.globals.project import (
    DEFAULT_TIMEOUT_SECONDS,
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)
from api.models import CityNameAlias
from brain.settings import TWO_SHIP_API_KEY, TWO_SHIP_BASE_URL


class TwoShipBase:
    """
    TwoShip Base Api Class
    """

    # Default Decimal Values
    _sig_fig = Decimal("0.01")
    _zero = Decimal("0.00")
    _one = Decimal("1.00")
    _hundred = Decimal("100.00")

    # 2Ship Api Values
    _bbe_yeg_ff_location_id = 4110
    _dimension_type_metric = 1
    _dimension_type_imperial = 0
    _weight_type_metric = 1
    _weight_type_imperial = 0
    _measurement_type_metric = 1
    _measurement_type_imperial = 0
    _pdf_document_type = 0
    _4x6_document_type = 1
    _prepaid_billing = 1
    _customer_packaging = 1
    _bill_customs_to_recipient = 2
    _deliver_duties_unpaid = 5
    _sold_purpose = 1
    _ground_service = 1
    _express_service = 0

    # Document Map to ubbe
    _label = 0
    _commercial_invoice = 1
    _bol = 2

    _document_map = {
        _label: DOCUMENT_TYPE_SHIPPING_LABEL,
        _bol: None,
        _commercial_invoice: DOCUMENT_TYPE_COMMERCIAL_INVOICE,
    }

    # 2Ship Endpoints
    _rate_url = TWO_SHIP_BASE_URL + "/api/Rate_V1"
    _ship_url = TWO_SHIP_BASE_URL + "/api/Ship_V1"
    _track_url = TWO_SHIP_BASE_URL + "/api/Tracking_V1"
    _pickup_url = TWO_SHIP_BASE_URL + "/api/CreatePickupRequest_V1"
    _delete_url = TWO_SHIP_BASE_URL + "/api/DeleteShipment_V1"
    _cancel_pickup = TWO_SHIP_BASE_URL + "/api/CancelPickupRequest_V1"
    _carrier_info_url = TWO_SHIP_BASE_URL + "/api/GetCarrierInfo_V1"

    def __init__(self, ubbe_request: dict):
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._api_key = TWO_SHIP_API_KEY

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    @staticmethod
    def _build_address(address: dict, carrier_id: int):
        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=carrier_id,
        )

        return {
            "Address1": address["address"],
            "Address2": address.get("address_two", "")[:25],
            "City": city[:30],
            "CompanyName": address["company_name"][:30],
            "Country": address["country"],
            "Email": "customerservice@ubbe.com",
            "IsResidential": not address.get("has_shipping_bays", True),
            "PersonName": address["name"][:30],
            "PostalCode": address["postal_code"],
            "State": address["province"],
            "Telephone": address["phone"],
            "TelephoneExtension": address.get("extension", ""),
        }

    @staticmethod
    def _get_total_of_key(items: list, key: str) -> Decimal:
        """
        Get total for item list for specific key
        :param items: List of dicts
        :param key: keyt o sum
        :return: Sum value
        """
        total = Decimal("0.00")

        for item in items:
            total += Decimal(str(item[key]))
        return total

    @staticmethod
    def _post(url: str, request: dict) -> Union[list, dict]:
        """
        Request 2Ship data for a request.
        :param request: 2Ship Request Dict
        :return: 2Ship Response
        """

        try:
            response = requests.post(
                url=url, json=request, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as e:
            CeleryLogger().l_info.delay(
                location="twoship_base.py line: 274",
                message=f"2Ship posting data: {request}",
            )
            connection.close()
            raise RequestError(None, request) from e

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return {
                "IsCanceled": True
            }

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_info.delay(
                location="twoship_base.py line: 274",
                message=f"2Ship Data: {request}\n Response: {response.text}",
            )
            connection.close()
            raise RequestError(response, request) from e

        # If 2Ship ever removes their stack trace, we might still be able to detect the exception message
        if "ExceptionMessage" in response:
            return {
                "ExceptionMessage": response["ExceptionMessage"],
                "IsError": True
            }
        elif "StackTrace" in response or "ExceptionMessage" in response:
            CeleryLogger().l_info.delay(
                location="twoship_base.py line: 274",
                message=f"2Ship Data: {request}\n Response: {response}",
            )
            connection.close()
            raise ViewException("2Ship Rate (L187): Stack Trace.")

        connection.close()

        if isinstance(response, list):
            return {
                "IsError": False,
                "Data": response
            }

        response["IsError"] = False
        return response
