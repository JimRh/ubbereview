"""
    Title: Purolator Freight Estimate
    Description: This file will contain helper functions related to Purolator Freight Estimate specs.
    Created: December 15, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

from api.apis.carriers.purolator.freight.helpers.packages import (
    PurolatorFreightPackages,
)
from api.apis.carriers.purolator.helpers.address import PurolatorAddress


class PurolatorFreightEstimate:
    """
    Purolator Freight Estimate
    """

    def __init__(self, ubbe_request: dict, is_rate: bool) -> None:
        self._ubbe_request = ubbe_request
        self._is_rate = is_rate
        self._puro_address = PurolatorAddress(
            is_rate=is_rate, ubbe_request=ubbe_request
        )
        self._puro_package = PurolatorFreightPackages(is_rate=is_rate)

    @staticmethod
    def _build_payment(account_number: str):
        """
        Build puro payment soap object.
        :param account_number:
        :return:
        """
        return {
            "PaymentType": "Sender",  # ThirdParty
            "BillingAccountNumber": account_number,
            "RegisteredAccountNumber": account_number,
        }

    def _build_address(self, address: dict) -> dict:
        """
         Build puro address soap object.
        :return:
        """

        ret = {
            "Address": self._puro_address.address(address=address),
            "EmailAddress": address.get("email", "no-reply@ubbe.com"),
        }

        return ret

    def _build_shipment_details(self) -> dict:
        """
         Build puro address soap object.
        :return:
        """

        ret = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "ServiceTypeCode": "S",
            "DeclaredValue": Decimal("0.00"),
            "CODAmount": Decimal("0.00"),
            "SpecialInstructions": self._ubbe_request.get("special_instructions", "")[
                :30
            ],
            "LineItemDetails": self._puro_package.packages(
                packages=self._ubbe_request["packages"]
            ),
        }

        return ret

    def estimate(self, account_number: str) -> dict:
        """
         Build puro shipment soap object.
        :param account_number:
        :return:
        """

        ret = {
            "SenderInformation": self._build_address(
                address=self._ubbe_request["origin"]
            ),
            "ReceiverInformation": self._build_address(
                address=self._ubbe_request["destination"]
            ),
            "PaymentInformation": self._build_payment(account_number=account_number),
            "ShipmentDetails": self._build_shipment_details(),
        }

        return ret
