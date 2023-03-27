"""
    Title: Action Express Ship Api
    Description: This file will contain functions related to Action Express Ship Apis.
    Created: June 14, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db import connection

from api.apis.carriers.action_express.endpoints.ac_api import ActionExpressApi
from api.apis.carriers.action_express.helpers.order import Order
from api.apis.carriers.action_express.helpers.price_modifiers import PriceModifier
from api.apis.services.taxes.taxes import Taxes
from api.exceptions.project import RequestError, ShipException
from api.globals.carriers import ACTION_EXPRESS
from api.utilities.date_utility import DateUtility


class ActionExpressShip(ActionExpressApi):
    """
    Action Express Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._ac_order = Order(ubbe_request=self._ubbe_request)
        self._response = {}

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    def _format_response(
        self, response: dict, service_name: str, service_cost: Decimal
    ):
        """
        Process Action Express tracking response for the latest status and format into ubbe shipment tracking
        status.
        :return: dict of latest tracking status
        """
        surcharges = []

        try:
            tax = Taxes(self._ubbe_request["destination"]).get_tax()
            tax_percent = tax.tax_rate
        except RequestError:
            tax_percent = Decimal("5")

        total_cost = Decimal(response["TotalCost"])
        tax_amount = Decimal(total_cost * (tax_percent / 100)).quantize(self._sig_fig)

        if self._ubbe_request["service_code"] in ["RUSH", "DOUBLE", "DIRECT"]:
            transit = self._same_day
            surcharges.append(
                {
                    "name": service_name,
                    "cost": service_cost,
                    "percentage": Decimal("0.00"),
                }
            )
        else:
            transit = self._transit_time

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request.get("pickup", {})
        ).get_estimated_delivery(
            transit=transit,
            country=self._ubbe_request["origin"]["country"],
            province=self._ubbe_request["origin"]["province"],
        )

        self._response = {
            "carrier_id": ACTION_EXPRESS,
            "carrier_name": self._carrier_name,
            "service_code": self._ubbe_request["service_code"],
            "service_name": service_name,
            "freight": Decimal(total_cost - service_cost).quantize(self._sig_fig),
            "surcharges": surcharges,
            "surcharges_cost": service_cost,
            "tax_percent": tax_percent,
            "taxes": tax_amount,
            "total": Decimal(total_cost + tax_amount).quantize(self._sig_fig),
            "tracking_number": response["TrackingNumber"],
            "pickup_id": "",
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
            "carrier_api_id": response["ID"],
        }

    def ship(self, order_number: str = "") -> dict:
        """
        Ship Action Express shipment.
        :param order_number: ubbe shipment id -> REMOVE PARAM.
        :return:
        """

        try:
            order = self._ac_order.create_order(
                customer=self._customer_id, price_set=self._price_set
            )
        except KeyError as e:
            connection.close()
            raise ShipException(
                code="27200", message=f"AE Ship (L74): {str(e)}", errors=[]
            ) from e

        try:
            order, service, service_cost = PriceModifier(
                order=order
            ).add_ship_modifiers(service_code=self._ubbe_request["service_code"])
        except KeyError as e:
            connection.close()
            raise ShipException(
                code="27201", message=f"AE Ship (L109): {str(e)}", errors=[]
            ) from e

        service_code, service_name = service.split(":")
        description = order["Description"]
        order["Description"] = f"{service_name}\n{description}"

        try:
            response = self._post(url=f"{self._url}/order/post", data=order)
        except RequestError as e:
            connection.close()
            raise ShipException(
                code="27202", message=f"AE Ship (L119): {str(e)}", errors=[]
            ) from e

        try:
            self._format_response(
                response=response, service_name=service_name, service_cost=service_cost
            )
        except Exception as e:
            connection.close()
            raise ShipException(
                code="27203", message=f"AE Ship (L125): {str(e)}", errors=[]
            ) from e

        connection.close()
        return self._response
