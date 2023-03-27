"""
    Title: ubbe ML Rate Carrier Api
    Description: TThis file will contain functions related to ubbe ML Rate Api.
    Created: Feb 15, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db import connection

from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_base import MLCarrierBase
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from api.utilities.date_utility import DateUtility


class MLCarrierRate(MLCarrierBase):
    """
    Class will handle all details about a BBE rate requests.
    """

    def __init__(self, ubbe_request: dict):
        super().__init__(ubbe_request=ubbe_request)
        self._response = []

    def _process_rate(self, freight, surcharge, tax, total):
        """
        Process the data into the correct response format
        :param freight: cost of freight
        :param surcharge: cost of surcharge
        :param tax: cost of tax
        :param total: total cost of the shipment
        """
        tax_percent = Decimal(((total / freight) - 1) * 100).quantize(2)

        estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
            transit=-1,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        self._response.append(
            {
                "carrier_id": 904,
                "carrier_name": self._carrier_name,
                "service_code": self._service,
                "service_name": self._service_name,
                "freight": freight,
                "surcharge": surcharge,
                "tax": tax,
                "tax_percent": tax_percent,
                "sub_total": Decimal(freight + surcharge).quantize(self._sig_fig),
                "total": total,
                "transit_days": transit,
                "delivery_date": estimated_delivery_date,
            }
        )

    def rate(self) -> list:
        """
        Gets rate for Machine Learning
        :return: List of ML Rates
        """

        if self._origin["province"] in ["YT", "NT", "NU"] or self._destination[
            "province"
        ] in ["YT", "NT", "NU"]:
            return []

        try:
            dist_location = self._get_distance(self._origin, self._destination)
        except ViewException as e:
            connection.close()
            CeleryLogger().l_info.delay(
                location="ube_ml_rate.py line: 55", message=str(e.message)
            )
            return []

        try:
            total_weight = self._ubbe_request["total_weight"]
            freight = Decimal(
                self.get_ml_price_cents(
                    float(total_weight), float(dist_location.distance)
                )
                / 100
            ).quantize(self._sig_fig)
            total, surcharge, tax = self._get_all_surcharges(freight)
            self._process_rate(freight, surcharge, tax, total)
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="ube_ml_rate.py line: 65", message=str(e)
            )
            return []

        return self._response
