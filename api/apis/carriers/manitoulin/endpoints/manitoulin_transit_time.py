"""
    Title: Manitoulin Transit Time Calculator Endpoint
    Description: This file will contain all functions to get the transit time between the origin and destination.
    Created: January 10, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import datetime

from django.db import connection

from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi

from api.exceptions.project import RequestError, ViewException
from api.utilities.date_utility import DateUtility


class ManitoulinTransitTime(ManitoulinBaseApi):
    """
    Manitoulin Rate Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._request = {}
        self._response = []

    def _get_pickup_date(self) -> str:
        """
        Gets pickup date from ubbe request or uses the current date/time
        :return: pickup date
        """

        pickup = self._ubbe_request.get("pickup", {})
        pickup_date = pickup.get("date")

        if not pickup_date:
            pickup_date = datetime.datetime.now() + datetime.timedelta(days=1)

        return pickup_date.strftime("%Y-%m-%d")

    def _build_transit_request(self):
        """
        Build request for the transit time calculator endpoint
        :return: params for the transit get request
        """
        origin = self._ubbe_request["origin"]
        destination = self._ubbe_request["destination"]
        pickup_date = self._get_pickup_date()
        service_parts = self._ubbe_request["service_code"].split("|")
        service_code = service_parts[0]

        params = {
            "origin_city": origin["city"],
            "origin_province": origin["province"],
            "destination_city": destination["city"],
            "destination_province": destination["province"],
            "pickup_date": pickup_date,
        }

        if service_code in ["ROCKA", "ROCKP"]:
            params["guaranteed_service"] = True
            params["guaranteed_service_option"] = service_code[-1]

        return params

    def get_transit_time(self, params: dict):
        """
        Gets all transit time info
        :param params:
        :return: transit time and delivery date
        """

        try:
            transit = self._get(url=self._transit_time_calculator_url, params=params)
            transit_time = int(transit["business_day"])

            delivery_date, transit_time = DateUtility().get_estimated_delivery(
                transit=transit_time,
                country=self._ubbe_request["origin"]["country"],
                province=self._ubbe_request["origin"]["province"],
            )
        except RequestError:
            transit_time = -1
            delivery_date = (
                datetime.datetime(year=1, month=1, day=1)
                .replace(microsecond=0, second=0, minute=0, hour=0)
                .isoformat()
            )

        ret = {"business_day": transit_time, "delivery_date": delivery_date}

        return ret

    def transit(self):
        """
        Get transit time for Manitoulin
        :return: transit time
        """

        try:
            request = self._build_transit_request()
        except Exception as e:
            connection.close()
            raise ViewException(
                "Manitoulin Transit Time (L198): Failed building request."
            ) from e

        try:
            transit_time = self.get_transit_time(params=request)
        except KeyError as e:
            connection.close()
            raise ViewException(
                f"Manitoulin Transit Time (L204): No Rates sending request {str(e)}."
            ) from e

        return transit_time
