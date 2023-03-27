"""
    Title: Purolator Shipment
    Description: This file will contain helper functions related to Purolator Shipment specs.
    Created: November 19, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from api.apis.carriers.purolator.helpers.address import PurolatorAddress
from api.apis.carriers.purolator.courier.helpers.packages import PurolatorPackages


class PurolatorShipment:
    """
    Purolator Shipment
    """

    def __init__(self, ubbe_request: dict, is_rate: bool) -> None:
        self._ubbe_request = ubbe_request
        self._is_rate = is_rate
        self._puro_address = PurolatorAddress(
            is_rate=is_rate, ubbe_request=ubbe_request
        )
        self._puro_package = PurolatorPackages(
            ubbe_request=ubbe_request, is_rate=is_rate
        )

    @staticmethod
    def _build_payment(account_number: str) -> dict:
        """
        Build puro payment soap object.
        :param account_number:
        :return:
        """
        return {
            "PaymentType": "Sender",  # ThirdParty
            "RegisteredAccountNumber": account_number,
            "BillingAccountNumber": account_number,
        }

    def _build_content_detail(self) -> list:
        """
        Build Content Details for package commodities.
        :return:
        """
        content = []

        for com in self._ubbe_request.get("commodities", []):
            content.append(
                {
                    "Description": com["description"],
                    "CountryOfManufacture": com["made_in_country_code"],
                    "UnitValue": com["unit_value"],
                    "Quantity": com["quantity"],
                    "USMCADocumentIndicator": False,
                    "TextileIndicator": False,
                    "TextileManufacturer": "",
                    "FCCDocumentIndicator": False,
                    "SenderIsProducerIndicator": False,
                }
            )

        return content

    def _build_address(self, address: dict, is_tax: bool) -> dict:
        """
         Build puro address soap object.
        :return:
        """

        ret = {"Address": self._puro_address.address(address=address)}

        if is_tax:
            ret.update({"TaxNumber": address.get("tax_number", "")})

        return ret

    def _build_international(self, broker: dict) -> dict:
        """
        Build International Configs
        :return:
        """
        return {
            # "ContentDetails": {
            #     "ContentDetail": self._build_content_detail()
            # },
            "DutyInformation": {
                "BillDutiesToParty": "Receiver",
                "BusinessRelationship": "NotRelated",
                "Currency": "CAD",
            },
            "PreferredCustomsBroker": broker["company_name"],
            "DocumentsOnlyIndicator": True,
            "ImportExportType": "Permanent",
            "CustomsInvoiceDocumentIndicator": False,
        }

    def _build_tracking_reference(self) -> dict:
        """
         Build puro tracking reference soap object.
        :return:
        """

        if self._ubbe_request.get("reference_one", ""):
            ref = f'{self._ubbe_request.get("order_number", "")}/{self._ubbe_request.get("reference_one", "")}'
        else:
            ref = self._ubbe_request.get("order_number", "")

        return {
            "Reference1": ref[:30],
            "Reference2": self._ubbe_request.get("reference_one", "")[:30],
            "Reference3": self._ubbe_request.get("reference_two", "")[:30],
            "Reference4": self._ubbe_request.get("project", "")[:30],
        }

    def shipment(self, account_number: str) -> dict:
        """
         Build puro shipment soap object.
        :param account_number:
        :return:
        """
        service = ""
        is_international = self._ubbe_request.get("is_international", False)

        if self._ubbe_request.get("service_code"):
            service = self._ubbe_request["service_code"]

        destination = self._build_address(
            address=self._ubbe_request["destination"], is_tax=True
        )

        if "awb" in self._ubbe_request:
            instructions = f'{self._ubbe_request["awb"]}/{self._ubbe_request.get("special_instructions", "")}'[
                :30
            ]
        else:
            instructions = self._ubbe_request.get("special_instructions", "")[:30]

        ret = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": self._build_address(
                address=self._ubbe_request["origin"], is_tax=True
            ),
            "ReceiverInformation": destination,
            "PackageInformation": self._puro_package.packages(service=service),
            "TrackingReferenceInformation": self._build_tracking_reference(),
            "PaymentInformation": self._build_payment(account_number=account_number),
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": instructions},
        }

        if is_international and not self._is_rate:
            ret.update(
                {
                    "InternationalInformation": self._build_international(
                        broker=self._ubbe_request["broker"]
                    )
                }
            )

        return ret
