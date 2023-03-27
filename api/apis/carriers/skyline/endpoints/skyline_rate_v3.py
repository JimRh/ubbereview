import copy
from decimal import Decimal, InvalidOperation
from typing import Union

import gevent
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.carriers.skyline.exceptions.exceptions import SkylineRateError
from api.apis.carriers.skyline.services.interlines import GetInterlineID
from api.apis.carriers.skyline.services.pickup_delivery_cost import PickupDeliveryCost
from api.apis.carriers.skyline.services.transit_time import Transit
from api.apis.carriers.skyline.endpoints.skyline_api_v3 import SkylineAPI
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, RateException
from api.globals.carriers import CAN_NORTH
from api.globals.project import getkey, DEFAULT_TIMEOUT_SECONDS
from api.utilities.date_utility import DateUtility


class SkylineRate(SkylineAPI):
    """
    Class will handle all details about a Skyline rate requests.
    """

    def __init__(self, gobox_request: dict):
        super(SkylineRate, self).__init__(gobox_request)
        self._response = []
        self._skyline_requests = []

    @staticmethod
    def _get_total_of_key(items, key) -> Decimal:
        """
        Gets the total for a key and its items.
        """
        if not isinstance(items, list):
            raise RateException({"api.error": "List is required"})
        total = Decimal("0.00")

        for item in items:
            price = item.get(key)
            if price is None:
                raise RateException({"api.error": "Invalid Key"})
            total += Decimal(str(price))

        return total

    @staticmethod
    def _parse_service(response) -> tuple:
        """
        Gets the service name and the rate priority ID from the skyline rate response
        """
        packages = getkey(response, "data.PackagePrices", {})

        service_id = packages[0].get("RatePriorityId", "")
        service_name = packages[0].get("RatePriorityName", "")

        return service_id, service_name

    def _add_pickup_delivery(self):
        """
        Gets the service name and the rate priority ID from the skyline rate response
        """
        origin_city = getkey(self._gobox_request, "origin.city", "")
        destination_city = getkey(self._gobox_request, "destination.city", "")

        p_and_d = PickupDeliveryCost(
            is_pickup=self._is_pickup,
            is_delivery=self._is_delivery,
            total_weight=self._total_weight,
            total_dim=self._total_dim,
            origin_city=origin_city,
            delivery_city=destination_city,
        )

        if self._is_pickup:
            charge = p_and_d.calculate_pickup()
        elif self._is_delivery:
            charge = p_and_d.calculate_delivery()
        else:
            raise RateException({"api.error.skyline.pickup": "Unknown option selected"})

        if not charge:
            raise RateException({"api.error.skyline.pickup": "Unknown option selected"})

        freight = charge.get("Charge", Decimal("0.00"))
        taxes = (freight * self._northern_tax_rate).quantize(self._sig_fig)

        return {
            "total": (freight + taxes).quantize(self._sig_fig),
            "freight": freight,
            "taxes": taxes,
            "service_name": charge["FeeName"],
        }

    def _get_pickup_or_delivery_cost(self):
        """
        Gets the pickup or delivery for a Canadian North location
        """
        try:
            costs = self._add_pickup_delivery()
        except RateException:
            return []

        tax_percentage = Decimal(
            (costs["taxes"] / costs["total"]) * Decimal("100.00")
        ).quantize(self._sig_fig)

        estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
            transit=1,
            country=self._gobox_request["origin"]["country"],
            province=self._gobox_request["origin"]["province"],
        )

        return [
            {
                "carrier_id": CAN_NORTH,
                "carrier_name": "Canadian North",
                "service_code": "PICK_DEL",
                "service_name": costs["service_name"],
                "freight": costs["freight"],
                "surcharge": Decimal("0.00"),
                "tax_percent": tax_percentage,
                "tax": costs["taxes"],
                "total": costs["total"],
                "transit_days": transit,
                "delivery_date": estimated_delivery_date,
            }
        ]

    def _parse_prices(self, response) -> dict:
        """
        Parse Skyline response to get total cost, total freight, total taxes, and total surcharges.
        """
        packages = getkey(response, "data.PackagePrices", [])
        taxes = getkey(response, "data.Taxes", [])
        surcharges = getkey(response, "data.Surcharges", [])

        if not packages or not taxes or not surcharges:
            raise RateException({"api.error": "A key is not found"})

        try:
            total_freight = self._get_total_of_key(packages, "Freight")
            total_taxes = self._get_total_of_key(taxes, "Amount")
            total_surcharges = self._get_total_of_key(surcharges, "Amount")
        except RateException:
            raise RateException({"api.error": "Convert on string of non-numeric value"})
        total_cost = getkey(response, "data.Total", 0.00)

        if taxes:
            tax_percentage = taxes[0]["Percentage"] * 100
        else:
            tax_percentage = Decimal(
                (total_taxes / total_cost) * Decimal("100.00")
            ).quantize(self._sig_fig)

        if not total_cost:
            raise RateException({"api.error": "A price value does not exist"})

        try:
            total_cost = Decimal(str(total_cost))
        except InvalidOperation:
            raise RateException({"api.error": "Convert on string of non-numeric value"})
        return {
            "TotalCost": total_cost,
            "TotalFreight": total_freight,
            "TotalTaxes": total_taxes,
            "TotalSurcharges": total_surcharges,
            "TaxPercentage": tax_percentage,
        }

    def copy_packages(self, rate_priority) -> list:
        """
        Copy processed packages for each rate request and add Rate Priority ID and Nature of Good ID to each
        package.
        """
        copied_packages = copy.deepcopy(self._processed_packages)

        for pack in copied_packages:
            is_envelope = pack.pop("is_env", False)
            nog_id = pack["NogId"]

            if pack.get("is_dangerous_good", False):
                nog_id = 24

            # pri and general nog
            if int(rate_priority) == 2 and int(nog_id) == 302:
                # pri and PRIORITY CARGO
                nog_id = 36

            try:
                nog = self._nature_of_goods.get(
                    rate_priority_id=rate_priority, nog_id=nog_id
                )
            except ObjectDoesNotExist as e:
                raise SkylineRateError(e)

            if nog.rate_priority_code == "ENV" and not is_envelope:
                raise SkylineRateError(
                    "Rate: Envelope service not available for weight over 2kg."
                )

            pack["RatePriorityId"] = str(rate_priority)
            pack["NatureOfGoodsId"] = nog.nog_id

        return copied_packages

    def get_rates(self) -> None:
        """
        Gevent each skyline rate request and format each skyline response to GoBox API format.
        """
        greenlets = []

        for request in self._skyline_requests:
            greenlets.append(gevent.Greenlet.spawn(self._post, request))

        gevent.joinall(greenlets)

        for greenlet in greenlets:
            try:
                self._response.append(greenlet.get())
            except Exception as e:
                continue

        try:
            self._format_response()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="SkylineRate.py line: 213",
                message="Error in return from skyline: {}".format(e.message),
            )
            self._response = []

    def rate(self) -> list:
        """
        The function will handle building the Skyline rate requests, posting each rate request, and returning
        the formatted rate response from Skyline. It also checks whether the Skyline API is active.
        """

        try:
            self._rate_priorities()
            self._process_packages()
        except RateException as e:
            CeleryLogger().l_critical.delay(
                location="SkylineRate.py line: 242",
                message="Skyline Rate: {}".format(e.message),
            )
            connection.close()
            return []

        if self._is_pickup:
            connection.close()
            return self._get_pickup_or_delivery_cost()

        if self._is_delivery:
            connection.close()
            return self._get_pickup_or_delivery_cost()

        try:
            self._build()
        except RateException:
            connection.close()
            return []

        try:
            self.get_rates()
        except RequestError as e:
            CeleryLogger().l_critical.delay(
                location="SkylineRate.py line: 259",
                message="Skyline Rate error: {}.".format(e),
            )
            connection.close()
            return []

        connection.close()
        return self._response

    # Override
    def _build(self) -> None:
        """
        Build each rate request for each rate priority that belongs to the skyline account.
        """
        skyline_requests = []
        interline_id = None

        rate_priorities = {nog.rate_priority_id for nog in self._nature_of_goods}
        origin_airport_code = getkey(self._gobox_request, "origin.base")
        destination_airport_code = getkey(self._gobox_request, "destination.base")

        if origin_airport_code is None or destination_airport_code is None:
            CeleryLogger().l_critical.delay(
                location="SkylineRate.py line: 272",
                message="Skyline Rate: The airbase cannot be found.",
            )
            raise RateException(
                {"api.error": "Skyline Rate: The airbase cannot be found."}
            )

        interline = GetInterlineID(
            origin=origin_airport_code, destination=destination_airport_code
        )
        is_interline = interline.check_interline_lane()

        if is_interline:
            interline_id = interline.get_interline_code()

            if not interline_id:
                raise RateException(
                    {"api.error": "Skyline Rate: The Interline cannot be found."}
                )

        for priority in rate_priorities:
            try:
                packages = self.copy_packages(rate_priority=priority)
            except SkylineRateError as e:
                CeleryLogger().l_info.delay(
                    location="SkylineRate.py line: 292",
                    message="Skyline: No NOG found. {}".format(e.message),
                )
                continue

            request = {
                "DestinationAirportCode": destination_airport_code,
                "OriginAirportCode": origin_airport_code,
                "TotalPackages": self._total_packages,
                "TotalWeight": self._total_weight,
                "CustomerId": str(self._skyline_account.customer_id),
                "Packages": packages,
                "API_Key": str(self._api_key),
            }

            if is_interline:
                request["InterlineGroupId"] = interline_id

            skyline_requests.append(request)

        self._skyline_requests = skyline_requests

    # Override
    def _format_response(self):
        """
        Parse Skyline responses into GoBox format. It will also check for any errors in the response.
        """
        parsed_responses = []
        origin_airport = getkey(self._gobox_request, "origin.base")
        destination_airport = getkey(self._gobox_request, "destination.base")

        for response in self._response:
            if response.get("status", "error") == "error":
                continue

            prices = self._parse_prices(response)
            service_id, service_name = self._parse_service(response)

            try:
                transit = Transit(
                    origin=origin_airport,
                    destination=destination_airport,
                    service_id=int(service_id),
                    service_code=service_name,
                ).transit_time()
            except Exception:
                transit = -1

            estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
                transit=transit,
                country=self._gobox_request["origin"]["country"],
                province=self._gobox_request["origin"]["province"],
            )

            parsed_responses.append(
                {
                    "carrier_id": CAN_NORTH,
                    "carrier_name": "Canadian North",
                    "service_code": str(service_id),
                    "service_name": service_name,
                    "freight": prices["TotalFreight"],
                    "surcharge": prices["TotalSurcharges"],
                    "tax": prices["TotalTaxes"],
                    "tax_percent": prices["TaxPercentage"],
                    "total": prices["TotalCost"],
                    "transit_days": transit,
                    "delivery_date": estimated_delivery_date,
                    "mid_o": copy.deepcopy(self._gobox_request["mid_o"]),
                    "mid_d": copy.deepcopy(self._gobox_request["mid_d"]),
                }
            )

        self._response = parsed_responses

    # Override
    def _post(self, data: dict) -> Union[list, dict]:
        """
        Make Skyline rate call
        """

        try:
            response = requests.post(
                self._rate_url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.RequestException as e:
            connection.close()
            CeleryLogger().l_info.delay(
                location="SkylineRate.py line: 345",
                message="Skyline Rate posting data: {}".format(data),
            )
            raise RequestError(None, data)

        if not response.ok:
            connection.close()
            CeleryLogger().l_info.delay(
                location="SkylineRate.py line: 353",
                message="Skyline Rate posting data: {} \nSkyline Rate return data: {}".format(
                    data, response.text
                ),
            )
            raise RequestError(response, data)

        try:
            response = response.json()
        except ValueError:
            connection.close()
            CeleryLogger().l_info.delay(
                location="SkylineRate.py line: 363",
                message="Skyline Rate posting data: {} \nSkyline Rate return data: {}".format(
                    data, response.text
                ),
            )
            raise RequestError(response, data)

        if response["errors"]:
            connection.close()
            CeleryLogger().l_info.delay(
                location="SkylineRate.py line: 371",
                message="Skyline Rate posting data: {} \nSkyline Rate return data: {}".format(
                    data, response
                ),
            )
            raise RequestError(None, data)

        return response
