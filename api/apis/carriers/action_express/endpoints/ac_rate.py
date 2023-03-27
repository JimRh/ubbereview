"""
    Title: Action Express Rate Api
    Description: This file will contain functions related to Action Express Rate Apis.
    Created: June 14, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

import pytz
from django.db import connection

from api.apis.carriers.action_express.endpoints.ac_api import ActionExpressApi
from api.apis.carriers.action_express.helpers.order import Order
from api.apis.carriers.action_express.helpers.price_modifiers import PriceModifier
from api.apis.services.taxes.taxes import Taxes
from api.exceptions.project import RequestError, RateException
from api.globals.carriers import ACTION_EXPRESS
from api.utilities.date_utility import DateUtility


class ActionExpressRate(ActionExpressApi):
    """
    Action Express Rate Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._ac_order = Order(ubbe_request=self._ubbe_request)
        self._response = []

    def _format_response(self, responses: list):
        """
        Process Action Express tracking response for the latest status and format into ubbe shipment tracking
        status.
        :return: dict of latest tracking status
        """
        tz = pytz.timezone("America/Edmonton")
        time = datetime.datetime.now(tz=tz).strftime("%H:%M")

        for response in responses:
            service_code, service_name = response["service"].split(":")

            try:
                tax = Taxes(self._ubbe_request["destination"]).get_tax()
                tax_percent = tax.tax_rate
            except (RequestError, Exception):
                tax_percent = Decimal("5")

            tax_amount = Decimal(response["cost"] * (tax_percent / 100)).quantize(
                self._sig_fig
            )

            if service_code in ["RUSH", "DOUBLE", "DIRECT"] or time < "12:00":
                transit = self._same_day
            else:
                transit = self._transit_time

            estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
                transit=transit,
                country=self._ubbe_request["origin"]["country"],
                province=self._ubbe_request["origin"]["province"],
            )

            self._response.append(
                {
                    "carrier_id": ACTION_EXPRESS,
                    "carrier_name": self._carrier_name,
                    "service_code": service_code,
                    "service_name": service_name,
                    "freight": Decimal(
                        response["cost"] - response["service_cost"]
                    ).quantize(self._sig_fig),
                    "surcharge": Decimal(response["service_cost"]),
                    "tax": tax_amount,
                    "tax_percent": tax_percent,
                    "total": Decimal(response["cost"] + tax_amount).quantize(
                        self._sig_fig
                    ),
                    "transit_days": transit,
                    "delivery_date": estimated_delivery_date,
                }
            )

    def rate(self) -> list:
        """
        Track Action Express shipment.
        :return:
        """

        responses = []

        if (
            self._ubbe_request["origin"]["province"] != "AB"
            and self._ubbe_request["destination"]["province"] != "AB"
        ):
            return []

        try:
            order = self._ac_order.create_order(
                customer=self._customer_id, price_set=self._price_set
            )
        except KeyError as e:
            connection.close()
            raise RateException(
                code="27100", message=f"AE Rate (L90): {str(e)}", errors=[]
            ) from e

        try:
            requests = PriceModifier(order=order).add_rate_modifiers()
        except KeyError as e:
            connection.close()
            raise RateException(
                code="27101", message=f"AE Rate (L103): {str(e)}", errors=[]
            ) from e

        for request, service, service_cost in requests:
            try:
                cost = self._post(url=f"{self._url}/order/getTotalCost", data=request)
            except RequestError as e:
                connection.close()
                raise RateException(
                    code="27102",
                    message=f"AE Rate (L111): {str(e)}, Data: {str(order)}",
                    errors=[],
                ) from e

            responses.append(
                {
                    "request": request,
                    "cost": Decimal(cost),
                    "service": service,
                    "service_cost": service_cost,
                }
            )

        try:
            self._format_response(responses=responses)
        except Exception as e:
            connection.close()
            raise RateException(
                code="27103", message=f"AE Rate (L106): {str(e)}", errors=[]
            ) from e

        connection.close()
        return self._response
