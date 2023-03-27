"""
    Title: 2Ship Ship api
    Description: This file will contain functions related to 2Ship ship Api.
    Created: January 10, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.db import connection

from api.apis.carriers.twoship.endpoints.twoship_base_v2 import TwoShipBase
from api.documents.commercial_invoice import CommercialInvoice
from api.exceptions.project import RequestError, ShipException, ViewException
from api.globals.carriers import DHL
from api.globals.project import (
    DOCUMENT_TYPE_OTHER_DOCUMENT,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)


class TwoShipShip(TwoShipBase):
    """
    2Ship Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._service_code = self._ubbe_request["service_code"]

    def _build_packages(self) -> list:
        """
        Build 2ship Package data from ubbe format.
        :return: List of 2ship package format
        """
        packages = []

        for package in self._ubbe_request["packages"]:
            if not self._ubbe_request.get("is_metric", True):
                length = package["imperial_length"]
                width = package["imperial_width"]
                height = package["imperial_height"]
                weight = package["imperial_weight"]
                dimension_type = self._dimension_type_imperial
                weight_type = self._weight_type_imperial
            else:
                length = package["length"]
                width = package["width"]
                height = package["height"]
                weight = package["weight"]
                dimension_type = self._dimension_type_metric
                weight_type = self._weight_type_metric

            ret = {
                "Packaging": self._customer_packaging,
                "SkidDescription": package["description"],
                "Length": length,
                "Width": width,
                "Height": height,
                "Weight": weight,
                "FreightClassId": package["freight_class"],
                "DimensionType": dimension_type,
                "WeightType": weight_type,
                "ShipmentId": self._ubbe_request["order_number"],
                "Reference1": self._ubbe_request.get("reference_one", ""),
                "Reference2": self._ubbe_request.get("reference_two", ""),
            }

            for _ in range(package["quantity"]):
                packages.append(copy.deepcopy(ret))

        return packages

    def _build_reference(self) -> dict:
        """
        Build 2Ship references form ubbe request.
        :return: 2Ship formatted References
        """

        reference_one = self._ubbe_request.get("reference_one", "")
        air_waybill = self._ubbe_request.get("awb", "")

        if air_waybill:
            reference_one = f"AWB {air_waybill}:{reference_one}"

        return {
            "ShipmentReference": reference_one,
            "ShipmentReference2": self._ubbe_request.get("reference_two", ""),
        }

    def _build_international(self) -> dict:
        """
        Build 2Ship International format from ubbe request.
        :return: 2Ship International format
        """

        ret = {
            "CustomsBillingOptions": {"BillingType": self._bill_customs_to_recipient},
            "Invoice": {
                "TermsOfSale": self._deliver_duties_unpaid,
                "Purpose": self._sold_purpose,
                "Currency": "CAD",
            },
        }

        if "broker" in self._ubbe_request:
            ret["Broker"] = {
                "CompanyName": self._ubbe_request["broker"]["company_name"],
                "Telephone": self._ubbe_request["broker"]["phone"],
                "Email": self._ubbe_request["broker"]["email"],
                "Address1": self._ubbe_request["broker"]["address"],
                "City": self._ubbe_request["broker"]["city"],
                "State": self._ubbe_request["broker"]["province"],
                "Country": self._ubbe_request["broker"]["country"],
                "PostalCode": self._ubbe_request["broker"]["postal_code"],
            }

        return ret

    def _build_commodities(self) -> dict:
        """
        Build 2Ship commodities format from ubbe request.
        :return: 2Ship commodities format
        """
        commodities = []

        for com in self._ubbe_request["commodities"]:
            commodities.append(
                {
                    "Quantity": com["quantity"],
                    "UnitValue": com["unit_value"],
                    "Description": com["description"],
                    "TotalWeight": com["total_weight"],
                    "MadeInCountryCode": com["made_in_country_code"],
                    "QuantityUnitOfMeasure": "E",
                }
            )

        return {"Commodities": commodities}

    def _build_request(self) -> dict:
        """
        Build 2Ship shipping request from ubbe reequst.
        :return: 2ship Ship Request
        """

        ret = {
            "WS_Key": self._api_key,
            "Billing": {"BillingType": self._prepaid_billing},
            "LocationId": self._bbe_yeg_ff_location_id,
            "LocationName": "YEGFF",
            "RetrieveBase64StringDocuments": True,
            "CarrierId": self._carrier_id,
            "ServiceCode": self._service_code,
            "OrderNumber": self._ubbe_request["order_number"],
            "Sender": self._build_address(
                address=self._ubbe_request["origin"], carrier_id=self._carrier_id
            ),
            "Recipient": self._build_address(
                address=self._ubbe_request["destination"], carrier_id=self._carrier_id
            ),
            "Packages": self._build_packages(),
            "LabelPrintPreferences": {
                "Encoding": self._pdf_document_type,
                "OutputFormat": self._4x6_document_type,
            },
            "ShipmentInstructions": self._ubbe_request["special_instructions"],
        }

        ret.update(self._build_reference())

        if self._ubbe_request["is_international"]:
            ret.update(self._build_international())

            ret["InternationalOptions"] = self._build_international()
            ret["Contents"] = self._build_commodities()

            if self._carrier_id == DHL:
                ret["ServiceCode"] = "P"

        return ret

    def _get_documents(self, documents: list) -> list:
        """
        Format 2Ship documents in ubbe format to be saved.
        :param documents: list of dicts of documents
        :return: ubbe format.
        """
        ret = []

        for document in documents:
            document_type = self._document_map.get(
                document["Type"], DOCUMENT_TYPE_OTHER_DOCUMENT
            )

            if document_type is None:
                continue

            if document_type == DOCUMENT_TYPE_COMMERCIAL_INVOICE:
                doc = CommercialInvoice(
                    self._ubbe_request, self._ubbe_request["order"]
                ).get_base_64()
            else:
                doc = document["DocumentBase64String"]

            ret.append({"document": doc, "type": document_type})

        if self._ubbe_request["is_dangerous_goods"]:
            documents.append(self._dg_service.generate_documents())

        return ret

    def _format_surcharges(self, client_price: dict) -> tuple:
        """
        Format 2Ship Surcharges response into ubbe format.
        :param client_price: Dict of carrier cost.
        :return: Total Surchages and list of surcharges.
        """
        surcharges_cost = Decimal("0.0")
        surcharges = []

        for surcharge in client_price["Surcharges"]:
            cost = Decimal(str(surcharge.get("Amount", self._zero)))
            surcharges_cost += cost

            surcharges.append(
                {"name": surcharge["Name"], "cost": cost, "percentage": self._zero}
            )

        if client_price.get("Fuel"):
            fuel = Decimal(str(client_price["Fuel"]["Amount"]))
            surcharges_cost += fuel
            surcharges.append(
                {
                    "name": "Fuel Surcharge",
                    "cost": fuel,
                    "percentage": (
                        Decimal(str(client_price["Fuel"]["Percentage"])) * self._hundred
                    ).quantize(self._sig_fig),
                }
            )

        return surcharges_cost, surcharges

    def _format_response(self, response: dict) -> dict:
        """
        Format 2Ship response into ubbe response to be saved.
        :param response: 2Ship Response.
        :return: ubbe format.
        """
        service = response["Service"]
        client_price = response["Service"]["ClientPrice"]

        surcharges_cost, surcharges = self._format_surcharges(client_price=client_price)

        freight = Decimal(str(client_price["Freight"])).quantize(self._sig_fig)
        tax = Decimal(str(client_price["TotalTaxes"])).quantize(self._sig_fig)
        tax_percent = self._get_total_of_key(client_price["Taxes"], "Percentage")
        total = Decimal(str(client_price["TotalPriceInSelectedCurrency"]))

        ret = {
            "carrier_id": self._carrier_id,
            "carrier_name": service["CarrierName"],
            "service_code": service["Service"]["Code"],
            "service_name": service["Service"]["Name"],
            "freight": freight,
            "surcharges": surcharges,
            "surcharges_cost": surcharges_cost.quantize(self._sig_fig),
            "tax_percent": tax_percent.quantize(self._sig_fig),
            "taxes": tax,
            "total": total.quantize(self._sig_fig),
            "tracking_number": response["TrackingNumber"],
            "pickup_id": "",
            "transit_days": service.get("TransitDays", -1),
            "delivery_date": service.get("DeliveryDate", ""),
            "carrier_api_id": response["ShipId"],
            "documents": self._get_documents(documents=response["ShipDocuments"]),
        }

        return ret

    def ship(self) -> dict:
        """
        Ship 2Ship shipment.
        :return:
        """

        if self._ubbe_request.get("carrier_options", []):
            connection.close()
            raise ShipException("2Ship Ship (L361):Carrier options not supported")

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise ShipException(f"2Ship Ship (L367): {str(e)}") from e

        try:
            response = self._post(url=self._ship_url, request=request)
        except ViewException as e:
            connection.close()
            raise ShipException(f"2Ship Ship (L367): {e.message}") from e
        except RequestError as e:
            connection.close()
            raise ShipException(f"2Ship Ship (L367): {str(e)}") from e

        if response["IsError"]:
            raise ShipException(f"2Ship Ship (L367): {str(response['ExceptionMessage'])}")

        try:
            response = self._format_response(response=response)
        except KeyError as e:
            connection.close()
            raise ShipException(f"2Ship Ship (L367): {str(e)}") from e

        return response

    def void(self) -> dict:
        """
        Void 2Ship Shipment.
        :return: Success Message
        """

        request = {
            "WS_Key": self._api_key,
            "DeleteType": 1,
            "TrackingNumber": self._ubbe_request["tracking_number"],
        }

        try:
            response = self._post(url=self._delete_url, request=request)
        except ViewException as e:
            connection.close()
            raise ShipException(f"2Ship Pickup (L367): {e.message}") from e
        except RequestError as e:
            connection.close()
            raise ShipException(f"2Ship Pickup (L367): {str(e)}") from e

        ret = {"is_canceled": True, "message": "Shipment Cancel."}

        return ret
