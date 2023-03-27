import copy
from decimal import Decimal

import gevent
from django.db import connection

from api.apis.carriers.bbe.endpoints.bbe_rate_v1 import BBERate
from api.apis.carriers.union.api_union_v2 import Union
from api.apis.multi_modal.rate_api import RateAPI
from api.apis.services.middle_location.middle_location import FindMiddleLocation
from api.exceptions.project import ViewException
from api.globals.carriers import UBBE_ML


class MultiCarrierGroundRate(RateAPI):

    def __init__(self, gobox_request: dict) -> None:
        super(MultiCarrierGroundRate, self).__init__(gobox_request)

        self._ground_carriers = []
        self._responses = []
        self._middle_location = None

        self._first_request = {}
        self._last_request = {}

    def _set_address(self, request: dict, key: str):
        """
            Update Origin or Destination address information to port.
            :param request: rate request.
            :param key: Key to update, ex: "Origin"
            :param port: Port Object
            :return:
        """
        request[key]["address"] = copy.deepcopy(self._middle_location["address"])
        request[key]["city"] = copy.deepcopy(self._middle_location["city"])
        request[key]["company_name"] = "GoBox API"
        request[key]["country"] = copy.deepcopy(self._middle_location["country"])
        request[key]["postal_code"] = copy.deepcopy(self._middle_location["postal_code"])
        request[key]["province"] = copy.deepcopy(self._middle_location["province"])
        request[key]["base"] = copy.deepcopy(self._middle_location["base"])

    def _build_request(self):
        """
            Build air multi legs and determine airbases for them.
            :return: None
        """

        try:
            self._middle_location = FindMiddleLocation().get_middle_location(
                origin=self._origin, destination=self._destination
            )
        except KeyError:
            raise ViewException("Error getting distance.")

        if not self._middle_location:
            connection.close()
            raise ViewException(message={
                "rate.mc_ground.error": f"No middle location found: {str(self._origin)} to {self._destination}."}
            )

        # Configure two requests
        self._first_request = copy.deepcopy(self._gobox_request)
        self._last_request = copy.deepcopy(self._gobox_request)
        self._set_address(request=self._first_request, key="destination")
        self._set_address(request=self._last_request, key="origin")

        self._first_request["carrier_id"] = self._ground_carriers
        self._last_request["carrier_id"] = self._ground_carriers

    def _process_carriers(self):
        """
            Separate the sealift carriers from ground carriers.
            :return: tuple of carrier lists
        """

        for carrier in self._carrier_id:
            if carrier in self._sealift_list + self._air_list + self._courier_list:
                continue

            if carrier == UBBE_ML:
                continue

            self._ground_carriers.append(carrier)

    @staticmethod
    def _get_cheapest(rate_data: list) -> dict:
        """

            :param rate_data:
            :return:
        """
        rate = min(rate_data, key=lambda l: l["total"])
        return rate

    @staticmethod
    def _apply_cross_dock(rate_data: dict):
        """

            :param rate_data:
            :return:
        """
        cost_dock = Decimal("100.0")
        rate_data["surcharge"] += cost_dock
        sub_total = rate_data["surcharge"] + rate_data["freight"]
        rate_data["tax"] = sub_total * (rate_data["tax_percent"] / 100)
        rate_data["total"] += sub_total + rate_data["tax"]

    def _send_requests(self):
        """

            :return:
        """
        bbe_rate = BBERate(ubbe_request=self._gobox_request).rate(is_quote=True)
        first_request = Union(gobox_request=self._first_request)
        last_request = Union(gobox_request=self._last_request)

        first_gevent = gevent.Greenlet.spawn(first_request.rate)
        last_gevent = gevent.Greenlet.spawn(last_request.rate)

        gevent.joinall([first_gevent, last_gevent])

        first_rate = first_gevent.get()
        last_rate = last_gevent.get()

        if not first_rate:
            first_rate = bbe_rate

        if not last_rate:
            last_rate = bbe_rate

        first_min = self._get_cheapest(rate_data=first_rate)
        last_min = self._get_cheapest(rate_data=last_rate)

        self._apply_cross_dock(rate_data=first_min)

        self._responses.append(([first_min], self._middle_location, [last_min]))

    def rate(self) -> list:
        self._process_carriers()

        if not self._ground_carriers:
            connection.close()
            raise ViewException(message={"rate.mc_ground.error": "No available carriers."})

        self._build_request()

        if not self._first_request or not self._last_request:
            connection.close()
            raise ViewException(message={"rate.mc_ground.error": "Error building requests"})

        self._send_requests()

        if not self._responses:
            connection.close()
            raise ViewException(message={"rate.mc_ground.error": "Error Retrieving Rates"})

        return self._responses
