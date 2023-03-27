"""
    Title: ubbe ML Ship Carrier Api
    Description: This file will contain functions related to Shipping.
    Created: February 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

import gevent
from django.db import connection

from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_base import MLCarrierBase
from api.documents.commercial_invoice import CommercialInvoice
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import ShipException, ViewException
from api.globals.carriers import UBBE_ML
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)
from api.models import Dispatch
from api.utilities.date_utility import DateUtility


class MLCarrierShip(MLCarrierBase):
    """
    ubbe ML Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._carrier_id = self._ubbe_request["carrier_id"]
        self._sub_account = self._ubbe_request["objects"]["sub_account"]
        self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
            self._carrier_id
        ]["account"]

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    def _get_documents(self) -> list:
        """
        Generate Documents: BOL, Cargo Labels. If needed: CI.
        :return: list of pdfs
        """
        is_international = self._ubbe_request["is_international"]
        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)
        bol_thread = gevent.Greenlet.spawn(manual_docs.generate_bol)

        piece_label_thread = gevent.Greenlet.spawn(manual_docs.generate_cargo_label)
        threads = [bol_thread, piece_label_thread]

        if is_international:
            commercial_invoice_thread = gevent.Greenlet.spawn(
                CommercialInvoice,
                self._ubbe_request,
                self._ubbe_request["order_number"],
            )
            threads.append(commercial_invoice_thread)

        gevent.joinall(threads)

        piece_label = piece_label_thread.value
        bol = bol_thread.value

        documents = [
            {"document": piece_label, "type": DOCUMENT_TYPE_SHIPPING_LABEL},
            {"document": bol, "type": DOCUMENT_TYPE_BILL_OF_LADING},
        ]

        if self._ubbe_request.get("is_dangerous_goods", False):
            documents.append(self._dg_service.generate_documents())

        if is_international:
            commercial_invoice = commercial_invoice_thread.value
            documents.append(
                {
                    "document": commercial_invoice,
                    "type": DOCUMENT_TYPE_COMMERCIAL_INVOICE,
                }
            )

        return documents

    def _get_dispatch(self) -> Dispatch:
        """
        Get dispatch for carrier city terminal, if none exist get the default one.
        :return:
        """
        return Dispatch.objects.get(carrier__code=UBBE_ML, is_default=True)

    def _process_surcharges(self, freight_cost: Decimal) -> tuple:
        """
        Process Shipment Surcharges
        :param freight_cost: Freight cost
        :return: tuple with surcharges, surcharges_cost, option_names
        """
        option_names = []
        final_weight = self._get_final_weight(self._carrier)
        surcharges = self._get_mandatory_options(self._carrier, freight_cost)
        surcharges.extend(
            self._get_carrier_options(
                carrier=self._carrier, freight_cost=freight_cost, is_metric=False
            )
        )
        surcharges_cost = Decimal("0.00")

        # Get Fuel Surcharge
        fuel_surcharge = self._get_fuel_surcharge_cost(
            carrier_id=self._carrier_id,
            final_weight=final_weight,
            freight_cost=freight_cost,
        )

        if fuel_surcharge["cost"] != self._zero:
            surcharges_cost += fuel_surcharge["cost"]
            surcharges.append(fuel_surcharge)

        for option in surcharges:
            option_names.append(option["name"])
            surcharges_cost += fuel_surcharge["cost"]

        return surcharges, surcharges_cost, option_names

    def ship(self, order_number: str = "") -> dict:
        """
        Ship a Machine Learning Shipment.
        :return: Shipment Details
        """

        try:
            dist_location = self._get_distance(self._origin, self._destination)
        except ViewException as e:
            connection.close()
            raise ShipException(
                {"api.error.ubbe_ml.ship": f"Error Getting distance: {str(e.message)}"}
            ) from e

        try:
            freight = Decimal(
                self.get_ml_price_cents(
                    float(self._ubbe_request["total_weight"]),
                    float(dist_location.distance),
                )
                / 100
            )
            surcharges, surcharges_cost, option_names = self._process_surcharges(
                Decimal(freight)
            )
        except ShipException as e:
            raise ShipException(
                {
                    "api.error.ubbe_ml.ship": f"Error Getting Freight or Surcharges: {str(e.message)}"
                }
            ) from e

        self._ubbe_request["bol"] = order_number
        self._ubbe_request["bol_number"] = order_number
        self._ubbe_request["tracking_number"] = order_number
        self._ubbe_request["option_names"] = option_names

        try:
            documents = self._get_documents()
        except ShipException as e:
            raise ShipException(
                {
                    "api.error.ubbe_ml.ship": f"Error fetching documents: {str(e.message)}"
                }
            ) from e

        taxes = self._get_taxes(freight, surcharges_cost)

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request.get("pickup")
        ).get_estimated_delivery(
            transit=-1,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        ship_return = {
            "carrier_id": UBBE_ML,
            "carrier_name": self._carrier_name,
            "documents": documents,
            "freight": Decimal(freight).quantize(self._sig_fig),
            "service_code": self._service,
            "service_name": self._service_name,
            "surcharges": surcharges,
            "surcharges_cost": Decimal(surcharges_cost).quantize(self._sig_fig),
            "taxes": Decimal(taxes).quantize(self._sig_fig),
            "tax_percent": (
                (taxes / (freight + surcharges_cost)) * self._hundred
            ).quantize(self._sig_fig),
            "sub_total": Decimal(freight + surcharges_cost).quantize(self._sig_fig),
            "total": Decimal(freight + surcharges_cost + taxes).quantize(self._sig_fig),
            "tracking_number": order_number,
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
        }

        return ship_return
