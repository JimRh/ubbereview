"""
    Title: Purolator Rate
    Description: This file will contain functions related to Purolator Rate Apis.
    Created: November 17, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db import connection
from lxml import etree
from zeep.exceptions import Fault

from api.apis.carriers.purolator.freight.helpers.estimate import (
    PurolatorFreightEstimate,
)
from api.apis.carriers.purolator.freight.purolator_freight_api import (
    PurolatorFreightApi,
)
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.carriers import PUROLATOR_FREIGHT
from api.models import API


class PurolatorFreightRate(PurolatorFreightApi):
    """
    Purolator Rate Class
    """

    _service = None

    def __init__(self, ubbe_request: dict) -> None:
        super(PurolatorFreightRate, self).__init__(ubbe_request=ubbe_request)
        self._puro_estimate = PurolatorFreightEstimate(
            is_rate=True, ubbe_request=self._ubbe_request
        )

        self.create_connection(wsdl_path="FreightEstimatingService.wsdl")
        self._service = self._client.create_service(
            "{http://purolator.com/pws/service/v1}EstimatingServiceEndpoint",
            f'{"https://devwebservices.purolator.com"}/EWS/V1/FreightEstimating/FreightEstimatingService.asmx',
        )

        self._response = []

    @staticmethod
    def _get_freight_cost(line_items: list):
        """
        Get surcharge cost from puro response for rate.
        :param surcharges: Puro surcharge list
        :return:
        """

        freight_cost = Decimal("0")

        for line in line_items:
            freight_cost += line["BasePrice"]

        return freight_cost

    def format_response(self, rate: dict) -> None:
        """
        Format each puro rate response into ubbe api response for rates.
        :param rates: Puro rate responses
        :return:
        """

        freight = self._get_freight_cost(line_items=rate["LineItemDetails"]["LineItem"])

        self._response.append(
            {
                "carrier_id": PUROLATOR_FREIGHT,
                "carrier_name": self._freight_name,
                "service_code": rate["TariffCode"],
                "service_name": self._puro_service.get(
                    rate["TariffCode"], self._freight_name
                ),
                "freight": freight,
                "surcharge": Decimal("0").quantize(Decimal("0.01")),
                "total": rate["TotalPrice"],
                "transit_days": rate["TransitDays"],
                "delivery_date": rate["EstimatedDeliveryDate"],
            }
        )

    def get_rate(self) -> dict:
        """
        Get puro rates for request. Either all rates or specific rate.
        :return:
        """

        estimate = self._puro_estimate.estimate(account_number=self._account_number)
        print(estimate)
        try:
            response = self._service.GetEstimate(
                _soapheaders=[
                    self._build_request_context(reference="GetEstimate", version="1.1")
                ],
                Estimate=estimate,
            )
        except (Fault, ValueError) as e:
            error = f"GetFullEstimate Error: {str(e)}, Data: {etree.tounicode(self._history.last_received['envelope'])}"
            CeleryLogger().l_warning.delay(
                location="purolator_rate.py line: 206",
                message=str(
                    {"api.error.purolator.rate": f"Zeep Failure: {str(error)}"}
                ),
            )
            return {}

        print(response)

        return response["body"]

    def rate(self) -> list:
        """
        Get Purolator Rates.
        :return:
        """

        if not API.objects.get(name="Purolator").active:
            connection.close()
            return []

        try:
            puro_rates = self.get_rate()
        except (RequestError, KeyError) as e:
            print(e)
            connection.close()
            return []

        if not puro_rates:
            print("?")
            connection.close()
            return []

        try:
            self.format_response(rate=puro_rates)
        except Exception as e:
            print(e)
            CeleryLogger().l_critical.delay(
                location="purolator_rate.py line: 240",
                message=f"Purolator Rate: {str(e)}",
            )
            connection.close()
            return []

        connection.close()
        return self._response
