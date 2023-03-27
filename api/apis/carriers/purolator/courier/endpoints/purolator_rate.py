"""
    Title: Purolator Rate
    Description: This file will contain functions related to Purolator Rate Apis.
    Created: November 17, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

from django.db import connection
from lxml import etree
from zeep.exceptions import Fault

from api.apis.carriers.purolator.courier.endpoints.purolator_base import (
    PurolatorBaseApi,
)
from api.apis.carriers.purolator.courier.helpers.shipment import PurolatorShipment
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.carriers import PUROLATOR
from brain.settings import PURO_BASE_URL


class PurolatorRate(PurolatorBaseApi):
    """
    Purolator Rate Class
    """

    _version = "2.2"
    _service = None

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._puro_shipment = PurolatorShipment(
            is_rate=True, ubbe_request=self._ubbe_request
        )

        self.create_connection(
            wsdl_path="EstimatingService.wsdl", version=self._version
        )
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v2}EstimatingServiceEndpointV2",
            f"{PURO_BASE_URL}/EWS/v2/Estimating/EstimatingService.asmx",
        )

        self._response = []

    @staticmethod
    def _get_tax(taxes: list, total: Decimal) -> dict:
        """
        Get tax cost from puro response for rate and ship.
        :param taxes: Puro tax list
        :param total: Puro total cost
        :return:
        """

        ret = {"tax": Decimal("0"), "tax_percent": Decimal("0")}

        for tax in taxes:
            if tax["Amount"] == Decimal("0"):
                continue

            ret["tax"] = tax["Amount"]
            sub_total = total - ret["tax"]
            ret["tax_percent"] = round(
                ret["tax"] / Decimal(str(sub_total)) * Decimal("100"), 0
            )
            break

        return ret

    @staticmethod
    def _get_surcharges(surcharges: list):
        """
        Get surcharge cost from puro response for rate.
        :param surcharges: Puro surcharge list
        :return:
        """

        surcharge_cost = Decimal("0")

        for surcharge in surcharges:
            surcharge_cost += surcharge["Amount"]

        return surcharge_cost

    @staticmethod
    def _get_surcharges_list(surcharges: list) -> tuple:
        """
        Get surcharge cost and surcharge list in ubbe formant from puro response for ship.
        :param surcharges: Puro surcharge list
        :return:
        """

        surcharge_list = []
        surcharge_cost = Decimal("0")

        for surcharge in surcharges:
            surcharge_cost += surcharge["Amount"]
            surcharge_list.append(
                {
                    "name": surcharge["Description"],
                    "cost": surcharge["Amount"],
                    "percentage": Decimal("0"),
                }
            )

        return surcharge_list, surcharge_cost

    @staticmethod
    def _get_option_prices(options: list):
        """
        Get option prices cost from puro response for rate.
        :param options: Puro options list
        :return:
        """

        option_cost = Decimal("0")

        for option in options:
            option_cost += option["Amount"]

        return option_cost

    @staticmethod
    def _get_option_prices_list(options: list):
        """
        Get option prices cost and option prices list in ubbe formant from puro response for ship.
        :param options: Puro option list
        :return:
        """

        option_list = []
        option_cost = Decimal("0")

        for option in options:
            option_cost += option["Amount"]
            option_list.append(
                {
                    "name": option["Description"],
                    "cost": option["Amount"],
                    "percentage": Decimal("0"),
                }
            )

        return option_list, option_cost

    def format_response(self, rates: list) -> None:
        """
        Format each puro rate response into ubbe api response for rates.
        :param rates: Puro rate responses
        :return:
        """
        origin = self._ubbe_request["origin"]["city"]
        destination = self._ubbe_request["destination"]["city"]

        for rate in rates:
            tax_info = self._get_tax(
                taxes=rate["Taxes"]["Tax"], total=rate["TotalPrice"]
            )
            surcharge_cost = self._get_surcharges(
                surcharges=rate["Surcharges"]["Surcharge"]
            )
            option_cost = self._get_option_prices(
                options=rate["OptionPrices"]["OptionPrice"]
            )

            if rate["EstimatedTransitDays"]:
                rate["EstimatedTransitDays"] = int(rate["EstimatedTransitDays"])
            else:
                rate["EstimatedTransitDays"] = -1

            if rate["ExpectedDeliveryDate"]:
                date = datetime.datetime.strptime(
                    rate["ExpectedDeliveryDate"], "%Y-%m-%d"
                )
                date = datetime.datetime.combine(
                    date, datetime.datetime.min.time()
                ).isoformat()
                rate["ExpectedDeliveryDate"] = date
            else:
                rate["ExpectedDeliveryDate"] = (
                    datetime.datetime.now()
                    .replace(microsecond=0, second=0, minute=0, hour=0)
                    .isoformat()
                )

            ret = {
                "carrier_id": PUROLATOR,
                "carrier_name": self._courier_name,
                "service_code": rate["ServiceID"],
                "service_name": self._puro_service.get(
                    rate["ServiceID"], self._courier_name
                ),
                "freight": rate["BasePrice"],
                "surcharge": Decimal(surcharge_cost + option_cost).quantize(
                    Decimal("0.01")
                ),
                "total": rate["TotalPrice"],
                "transit_days": rate["EstimatedTransitDays"],
                "delivery_date": rate["ExpectedDeliveryDate"],
                "origin": origin,
                "destination": destination,
            }

            ret.update(tax_info)

            self._response.append(ret)

    def format_response_single(self, rates: list):
        """
        Format individual puro rate response into ubbe api response for ship.
        :param rates: Puro rate response
        :return:
        """
        individual = rates[0]

        tax_info = self._get_tax(
            taxes=individual["Taxes"]["Tax"], total=individual["TotalPrice"]
        )
        surcharge_list, surcharge_cost = self._get_surcharges_list(
            surcharges=individual["Surcharges"]["Surcharge"]
        )
        option_list, option_cost = self._get_option_prices_list(
            options=individual["OptionPrices"]["OptionPrice"]
        )

        if individual["EstimatedTransitDays"]:
            individual["EstimatedTransitDays"] = int(individual["EstimatedTransitDays"])
        else:
            individual["EstimatedTransitDays"] = -1

        if individual["ExpectedDeliveryDate"]:
            date = datetime.datetime.strptime(
                individual["ExpectedDeliveryDate"], "%Y-%m-%d"
            )
            date = datetime.datetime.combine(
                date, datetime.datetime.min.time()
            ).isoformat()
            individual["ExpectedDeliveryDate"] = date
        else:
            individual["ExpectedDeliveryDate"] = (
                datetime.datetime.now()
                .replace(microsecond=0, second=0, minute=0, hour=0)
                .isoformat()
            )

        ret = {
            "freight": individual["BasePrice"],
            "surcharges": surcharge_list + option_list,
            "surcharge": Decimal(surcharge_cost + option_cost).quantize(
                Decimal("0.01")
            ),
            "tax": tax_info["tax"],
            "tax_percent": tax_info["tax_percent"],
            "total": individual["TotalPrice"],
            "transit_days": individual["EstimatedTransitDays"],
            "delivery_date": individual["ExpectedDeliveryDate"],
        }

        return ret

    def get_rate(self, is_all_rate: bool = True) -> list:
        """
        Get puro rates for request. Either all rates or specific rate.
        :return:
        """

        shipment = self._puro_shipment.shipment(account_number=self._account_number)

        try:
            response = self._service.GetFullEstimate(
                _soapheaders=[
                    self._build_request_context(
                        reference="GetFullEstimate", version="2.2"
                    )
                ],
                Shipment=shipment,
                ShowAlternativeServicesIndicator=is_all_rate,
            )
        except (Fault, ValueError) as e:
            error = f"GetFullEstimate Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_critical.delay(
                location="purolator_rate.py line: 206",
                message=str(
                    {"api.error.purolator.rate": f"Zeep Failure: {str(error)}"}
                ),
            )
            return []

        return response["body"]["ShipmentEstimates"]["ShipmentEstimate"]

    def rate(self) -> list:
        """
        Get Purolator Rates.
        :return:
        """

        try:
            puro_rates = self.get_rate(is_all_rate=True)
        except (RequestError, KeyError) as e:
            CeleryLogger().l_critical.delay(
                location="purolator_rate.py line: 230",
                message=f"Purolator Rate: {str(e)}",
            )
            connection.close()
            return []

        if not puro_rates:
            connection.close()
            return []

        try:
            self.format_response(rates=puro_rates)
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="purolator_rate.py line: 244",
                message=f"Purolator Rate: {str(e)}",
            )
            connection.close()
            return []

        connection.close()
        return self._response
