"""
    Title: Manitoulin Rate api
    Description: This file will contain functions related to Manitoulin rate Api.
    Created: December 22, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal, ROUND_UP

import gevent
import requests
from django.core.cache import cache
from django.db import connection

from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi
from api.apis.carriers.manitoulin.endpoints.manitoulin_transit_time import (
    ManitoulinTransitTime,
)

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RateException, RequestError, ViewException
from api.globals.carriers import MANITOULIN
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import CityNameAlias
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ManitoulinRate(ManitoulinBaseApi):
    """
    Manitoulin Rate Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._request = {}
        self._response = []

    def _build_contact(self) -> dict:
        """
        Build Manitoulin Contact from ubbe contact.
        :return: dictionary of Manitoulin Contact
        """

        ret = {
            "name": "Customer Service",
            "company": "BBE EXPEDITING LTD",
            "contact_method": "E",
            "contact_method_value": "customerservice@ubbe.com",
            "shipment_type": "ROAD",
            "shipment_terms": self._payment_terms,
        }

        return ret

    def _build_rate_address(self, key: str, address: dict) -> dict:
        """
        Build Manitoulin Origin/Destination from ubbe origin/destination.
        :return: dictionary of Manitoulin Origin/Destination
        """

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=MANITOULIN,
        )

        ret = {
            "city": city,
            "province": address["province"],
            "postal_zip": address["postal_code"],
        }

        ret.update(self._build_address_options(key))

        return ret

    def _build_address_options(self, address_type) -> dict:
        """
        Build Manitoulin rate quote option list with ubbe option codes.
        :return: Manitoulin Rate options
        """
        options = self._ubbe_request.get("carrier_options", [])
        key_type = "pickup" if address_type == "origin" else "delivery"

        ret = {
            f"tailgate_{key_type}": False,
            f"inside_{key_type}": False,
        }

        if address_type == "origin":
            ret["residential_pickup"] = not self._ubbe_request["origin"].get(
                "has_shipping_bays", True
            )

        if address_type == "destination":
            ret["residential_delivery"] = not self._ubbe_request["destination"].get(
                "has_shipping_bays", True
            )

        for option in options:
            if option == self._inside_pickup and address_type == "origin":
                ret[f"inside_{key_type}"] = True
            elif option == self._inside_delivery and address_type == "destination":
                ret[f"inside_{key_type}"] = True
            elif option == self._power_tailgate_pickup and address_type == "origin":
                ret[f"inside_{key_type}"] = True
            elif (
                option == self._power_tailgate_delivery
                and address_type == "destination"
            ):
                ret[f"inside_{key_type}"] = True

        return ret

    def _build_packages(self):
        """
        Build Manitoulin Packages from ubbe packages.
        :return: dictionary of Manitoulin Packages
        """

        package_list = []

        for package in self._ubbe_request["packages"]:
            qty = Decimal(package["quantity"])
            total_weight = Decimal(qty * package["imperial_weight"]).quantize(
                Decimal("1"), rounding=ROUND_UP
            )

            package_list.append(
                {
                    "class_value": self._freight_class_map[
                        package.get("freight_class", "70.00")
                    ],
                    "pieces": package["quantity"],
                    "description": package["description"],
                    "package_code_value": self._quote_package_type_map[
                        package["package_type"]
                    ],
                    "total_weight": int(total_weight),
                    "weight_unit_value": "LBS",
                    "length": int(
                        package["imperial_length"].quantize(
                            Decimal("1"), rounding=ROUND_UP
                        )
                    ),
                    "height": int(
                        package["imperial_height"].quantize(
                            Decimal("1"), rounding=ROUND_UP
                        )
                    ),
                    "width": int(
                        package["imperial_width"].quantize(
                            Decimal("1"), rounding=ROUND_UP
                        )
                    ),
                    "unit_value": "I",
                }
            )

        return package_list

    def _build_other(self):
        """
        Build "other" dict for the request.
        :return: dict of other fields
        """

        ret = {
            "currency_type": "C",
            "dangerous_goods": self._ubbe_request["is_dangerous_goods"],
        }

        for option in self._ubbe_request.get("carrier_options", []):
            if option == self._delivery_appointment:
                ret["delivery_by_appointment"] = True
            elif option == self._heated_truck:
                ret["protective_services_heat"] = True
            elif option == self._refrigerated_truck:
                ret["protective_services_reefer"] = True

        return ret

    def _build_request(self) -> {}:
        """
        Build Manitoulin rate request Dictionary
        :return: Manitoulin Rate Request Dictionary
        """

        ret = {
            "contact": self._build_contact(),
            "origin": self._build_rate_address("origin", self._ubbe_request["origin"]),
            "destination": self._build_rate_address(
                "destination", self._ubbe_request["destination"]
            ),
            "items": self._build_packages(),
            "other": self._build_other(),
            "service_code": "LTL",
        }

        return ret

    def _create_rock_solid_services(self, request: dict) -> list:
        """
        Build Manitoulin rate request Dictionary for rock solid services
        :return: Manitoulin Rock Solid Rate Request Dictionary
        """
        rock_requests = [request]

        for service in [
            self._rock_solid_afternoon_service,
            self._rock_solid_evening_service,
        ]:
            rock_request = copy.deepcopy(request)
            rock_request["other"]["rock_solid_service_guarantee"] = True
            rock_request["other"]["rock_solid_service_value"] = service
            rock_request["service_code"] = f"ROCK{service}"
            rock_requests.append(rock_request)

        return rock_requests

    def _format_response(self, responses: list) -> list:
        """
        Format rates returned from manitoulin rate quote request into ubbe format.
        :param response:
        :return: list of rates in ubbe format
        """
        if not responses:
            return []

        rate_responses = []

        for rate in responses:
            self._ubbe_request["service_code"] = rate["service_code"]

            if "id" not in rate:
                continue

            total_tax = Decimal(rate["federal_tax"]) + Decimal(rate["provincial_tax"])
            total_tax_percentage = Decimal(rate["federal_tax_percentage"]) + Decimal(
                rate["provincial_tax_percentage"]
            )

            fuel_surcharge = Decimal(rate["fuel_charge"])
            surcharge = Decimal(rate["total_accessorial_charge"])

            try:
                transit = ManitoulinTransitTime(self._ubbe_request).transit()
                transit_time = transit["business_day"]
                est_delivery_date = transit["delivery_date"]
            except ViewException as e:
                transit_time = -1
                est_delivery_date = (
                    datetime.datetime(year=1, month=1, day=1)
                    .replace(microsecond=0, second=0, minute=0, hour=0)
                    .isoformat()
                )

            ret = {
                "carrier_id": MANITOULIN,
                "carrier_name": self._carrier_name,
                "service_code": f'{rate["service_code"]}|{rate["quote"]}',
                "service_name": self._services[rate["service_code"]],
                "freight": Decimal(rate["freight_subtotal"]).quantize(self._sig_fig),
                "surcharge": Decimal(surcharge + fuel_surcharge).quantize(
                    self._sig_fig
                ),
                "surcharge_list": [],
                "tax": total_tax,
                "tax_percent": total_tax_percentage * Decimal("100"),
                "total": Decimal(rate["total_charge"]).quantize(self._sig_fig),
                "transit_days": transit_time,
                "delivery_date": est_delivery_date,
            }

            cache.set(
                f'{MANITOULIN}-{rate["quote"]}-{rate["service_code"]}',
                ret,
                TWENTY_FOUR_HOURS_CACHE_TTL,
            )
            del ret["surcharge_list"]

            rate_responses.append(ret)

        return rate_responses

    def _post(self, url: str, request: dict):
        """
        Make Manitoulin post api call.
        :param url, request:
        :return: response from post request
        """
        service_code = request.pop("service_code")

        try:
            response = requests.post(
                url=url,
                json=request,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                headers=self._get_auth(),
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(
                None, {"url": self._rate_url, "error": str(e), "data": request}
            ) from e

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_debug.delay(
                location="man_rate.py line: 388", message=f"{response.text}"
            )
            connection.close()
            raise RequestError(
                response, {"url": self._rate_url, "error": str(e), "data": request}
            ) from e

        if isinstance(response, list):
            CeleryLogger().l_debug.delay(
                location="man_rate.py line: 388", message=f"{str(request)}{response}"
            )
            raise RequestError(
                None,
                {
                    "url": self._rate_url,
                    "error": f"Manitoulin Error: {str(response)}",
                    "data": request,
                },
            )

        response["service_code"] = service_code

        connection.close()
        return response

    def _get_rates(self, rock_requests: list) -> list:
        """
        Gets LTL and rock solid rates at the same time
        :param request: requests
        :return: returns all rates in ubbe format
        """

        threads = []
        rates = []
        for request in rock_requests:
            threads.append(gevent.Greenlet.spawn(self._post, self._rate_url, request))

        gevent.joinall(threads)

        for thread in threads:
            try:
                rate = thread.get()
            except (RateException, RequestError):
                continue

            rates.append(rate)

        return self._format_response(responses=rates)

    def rate(self) -> list:
        """
        Get rates for Manitoulin Api
        :return: list of rate dictionaries in ubbe format
        """

        if (
            self._ubbe_request["origin"]["province"] == "NU"
            or self._ubbe_request["destination"]["province"] == "NU"
        ):
            connection.close()
            raise RateException("Manitoulin Rate (L187): Not Supported Region.")

        try:
            request = self._build_request()
        except RateException as e:
            connection.close()
            raise RateException(
                f"Manitoulin Rate (L198): Failed building request. {e.message}"
            ) from e

        rock_requests = self._create_rock_solid_services(request=request)

        try:
            rates = self._get_rates(rock_requests=rock_requests)
        except RequestError as e:
            connection.close()
            raise RateException(
                f"Manitoulin Rate (L204): Rates sending request {str(e)}."
            ) from e

        return rates
