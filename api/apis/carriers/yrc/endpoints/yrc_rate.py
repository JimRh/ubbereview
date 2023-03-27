"""
    Title: YRC Rate api
    Description: This file will contain functions related to YRC rate Api.
    Created: January 17, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
import math
from decimal import Decimal

import gevent
from django.core.cache import cache
from django.db import connection

from api.apis.carriers.yrc.endpoints.yrc_base import YRCBaseApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RateException, RequestError
from api.globals.carriers import YRC
from api.models import CityNameAlias
from api.utilities.date_utility import DateUtility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class YRCRate(YRCBaseApi):
    """
    YRC Fright Rate Class
    """

    _north = ["NT", "NU", "YT"]

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._request = {}
        self._response = []

    def _build_address(self, address: dict) -> dict:
        """
        Build YRC rate quote address dictionary for passed in address.
        :param address: Address dictionary
        :return: YRC Address Request
        """

        country = address["country"]

        if country == self._US:
            country = self._USA
        elif country == self._MX:
            country = self._MEX
        else:
            country = self._CAN

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=YRC,
        )

        return {
            "city": city,
            "state": address["province"],
            "postalCode": address["postal_code"],
            "country": country,
        }

    def _build_options(self, options: list) -> dict:
        """
        Build YRC rate quote option list with ubbe option codes.
        :return: YRC Rate optopns
        """
        option_list = []

        if not self._ubbe_request["origin"].get("has_shipping_bays", True):
            option_list.append(self._yrc_residential_pickup)

        if not self._ubbe_request["destination"].get("has_shipping_bays", True):
            option_list.append(self._yrc_residential_delivery)

        if not options:
            return {"accOptions": option_list}

        for option in options:
            if option == self._inside_pickup:
                option_list.append(self._yrc_inside_pickup)
            elif option == self._inside_delivery:
                option_list.append(self._yrc_inside_delivery)
            elif option == self._power_tailgate_pickup:
                option_list.append(self._yrc_power_tailgate_pickup)
            elif option == self._power_tailgate_delivery:
                option_list.append(self._yrc_power_tailgate_delivery)
            elif option == self._delivery_appointment:
                option_list.append(self._yrc_delivery_appointment)
            # elif option == self._heated_truck:
            #     option_list.append(self._yrc_protect_from_freezing)

        return {"accOptions": option_list}

    def _build_packages(self, packages: list) -> dict:
        """
        Build YRC package dictionary for rate quote request
        :param packages: ubbe package list.
        :return: YRC list of commodities dictionary
        """

        package_list = []

        for package in packages:
            package_code = "SKD"

            if package["package_type"] == "DRUM":
                package_code = "DRM"

            freight_class = self._freight_class_map[
                package.get("freight_class", "70.00")
            ]

            package_list.append(
                {
                    "packageCode": package_code,
                    "nmfcClass": freight_class,
                    "handlingUnits": package["quantity"],
                    "packageLength": math.ceil(int(package["imperial_length"])),
                    "packageWidth": math.ceil(int(package["imperial_width"])),
                    "packageHeight": math.ceil(int(package["imperial_height"])),
                    "weight": math.ceil(
                        int(package["imperial_weight"]) * package["quantity"]
                    ),
                }
            )

        return {"commodity": package_list}

    def _create_request(self) -> dict:
        """
        Build YRC rate quote request.
        :return: rate request
        """

        today = datetime.datetime.today() + datetime.timedelta(days=1)

        ret = {
            "login": self._build_json_auth(),
            "originLocation": self._build_address(address=self._ubbe_request["origin"]),
            "destinationLocation": self._build_address(
                address=self._ubbe_request["destination"]
            ),
            "details": {
                "serviceClass": self._std_service,
                "typeQuery": self._quote_type,
                "pickupDate": today.strftime("%Y%m%d"),
                "currency": "CAD",
                "acceptTerms": True,
            },
            "listOfCommodities": self._build_packages(
                packages=self._ubbe_request["packages"]
            ),
            "serviceOpts": self._build_options(
                options=self._ubbe_request.get("carrier_options", [])
            ),
        }

        return ret

    def _create_request_time_critical(self, request: dict) -> tuple:
        """
        Build YRC rate quote request.
        :return: rate request
        """
        if "pickup" in self._ubbe_request:
            pickup_date = self._ubbe_request["pickup"]["date"]
        else:
            pickup_date = datetime.datetime.today().date()

        time_critical = copy.deepcopy(request)
        destination = self._ubbe_request["destination"]
        delivery_date = pickup_date + datetime.timedelta(days=7)

        delivery_date = DateUtility().next_business_day(
            country_code=destination["country"],
            prov_code=destination["province"],
            in_date=delivery_date,
        )

        time_critical["details"]["serviceClass"] = self._tcsa_service
        time_critical["details"]["deliveryDate"] = delivery_date.replace("-", "")

        time_critical_5 = copy.deepcopy(time_critical)
        time_critical_5["details"]["serviceClass"] = self._tcsp_service

        return time_critical, time_critical_5

    def _format_surcharges(self, line_items: list) -> tuple:
        """
        Format surcharges into ubbe format for ship api.
        :param line_items:
        :return:
        """
        surcharges = []

        tax_info = {
            "name": "No Tax",
            "cost": Decimal("0.00"),
            "percentage": Decimal("0.00"),
        }

        for item in line_items:
            if item["type"] != "CodeWord" or item["code"] in [
                "DISC",
                "PROA",
                "TTL",
                "DIM",
                "AS",
            ]:
                continue

            if item.get("rateUOM", "") == "%":
                percentage = Decimal(Decimal(item["rate"]) / self._hundred).quantize(
                    self._sig_fig
                )
            else:
                percentage = self._zero

            ret = {
                "name": f'{item["description"]} ({item["code"]})',
                "cost": Decimal(Decimal(item["charges"]) / self._hundred).quantize(
                    self._sig_fig
                ),
                "percentage": percentage,
            }

            if item["code"] in ["GST", "HST"]:
                tax_info = ret
            else:
                surcharges.append(ret)

        return surcharges, tax_info

    def _format_response(self, response: dict, service_code: str) -> dict:
        """
        Format rates returned from yrc rate quote request into ubbe format.
        :param response:
        :return:
        """

        if not response["isSuccess"]:
            raise RateException(
                f'YRC Rate (L204): Rate Failed {str(response["errors"])}.'
            )

        page_root = response["pageRoot"]

        if page_root["returnCode"] != self._success:
            raise RateException(
                f'YRC Rate (L204): Rate Failed {page_root["returnText"]}.'
            )

        details = page_root["bodyMain"]["rateQuote"]

        if "quoteId" not in details:
            raise RateException(
                f'YRC Rate (L204): Rate Failed {page_root["returnText"]}.'
            )

        quote_id = details["quoteId"]
        delivery = details["delivery"]
        rate_charges = details["ratedCharges"]
        service_type = delivery["requestedServiceType"]

        transit = (
            delivery["standardDays"]
            if "standardDays" in delivery
            else self._default_transit
        )
        est_delivery_date = str(delivery.get("standardDate", ""))

        if est_delivery_date and est_delivery_date != "0":
            est_delivery_date = datetime.datetime.strptime(
                str(est_delivery_date), "%Y%m%d"
            ).isoformat()
        else:
            est_delivery_date, transit = DateUtility().get_estimated_delivery(
                transit=transit,
                country=self._ubbe_request["origin"]["country"],
                province=self._ubbe_request["origin"]["province"],
            )

        service_name = service_type["value"]

        if "level" in service_type:
            service_name = f'{service_name} {service_type["level"]}'.title()

        if service_name == self._service_spot:
            service_name = self._service_name_spot

        freight = Decimal(rate_charges["freightCharges"]) / self._hundred
        surcharge = Decimal(rate_charges["otherCharges"]) / self._hundred
        total = Decimal(rate_charges["totalCharges"]) / self._hundred
        surcharge_list, tax_info = self._format_surcharges(
            line_items=details["lineItem"]
        )

        ret = {
            "carrier_id": YRC,
            "carrier_name": self._carrier_name,
            "service_code": f"{service_code}|{quote_id}",
            "service_name": service_name,
            "freight": Decimal(freight).quantize(self._sig_fig),
            "surcharge": Decimal(surcharge).quantize(self._sig_fig),
            "surcharge_list": surcharge_list,
            "tax": tax_info["cost"],
            "tax_percent": tax_info["percentage"],
            "total": Decimal(total).quantize(self._sig_fig),
            "transit_days": transit,
            "delivery_date": est_delivery_date,
        }

        cache.set(f"{YRC}-{quote_id}-{service_code}", ret, TWENTY_FOUR_HOURS_CACHE_TTL)

        del ret["surcharge_list"]

        return ret

    def _get_rates(
        self,
        request: dict,
        time_critical_noon_request: dict,
        time_critical_5_request: dict,
    ):
        """

        :param request:
        :return:
        """
        rates = []

        standard = gevent.Greenlet.spawn(self._post, self._rate_url, request)
        time_critical = gevent.Greenlet.spawn(
            self._post, self._rate_url, time_critical_noon_request
        )
        time_critical_5 = gevent.Greenlet.spawn(
            self._post, self._rate_url, time_critical_5_request
        )

        gevent.joinall([standard, time_critical, time_critical_5])

        try:
            standard = standard.get()
        except Exception:
            standard = {"isSuccess": False, "errors": "Error YRC Rate"}

        try:
            time_critical = time_critical.get()
        except Exception:
            time_critical = {"isSuccess": False, "errors": "Error YRC Rate"}

        try:
            time_critical_5 = time_critical_5.get()
        except Exception:
            time_critical = {"isSuccess": False, "errors": "Error YRC Rate"}

        try:
            std_rates = self._format_response(
                response=standard, service_code=self._std_service
            )
        except RateException as e:
            CeleryLogger().l_info.delay(
                location="yrc_rate.py line: 305",
                message=str({"api.error.yrc.rate": e.message}),
            )
            std_rates = []

        try:
            time_critical = self._format_response(
                response=time_critical, service_code=self._tcsa_service
            )
        except RateException as e:
            CeleryLogger().l_info.delay(
                location="yrc_rate.py line: 305",
                message=str({"api.error.yrc.rate": e.message}),
            )
            time_critical = []

        try:
            time_critical_5 = self._format_response(
                response=time_critical_5, service_code=self._tcsp_service
            )
        except RateException as e:
            CeleryLogger().l_info.delay(
                location="yrc_rate.py line: 305",
                message=str({"api.error.yrc.rate": e.message}),
            )
            time_critical_5 = []

        if std_rates:
            rates.append(std_rates)

        if time_critical:
            rates.append(time_critical)

        if time_critical_5:
            rates.append(time_critical_5)

        if not std_rates:
            request["details"]["serviceClass"] = self._spot_quote
            request["details"]["pickupDate"] = datetime.datetime.today().strftime(
                "%Y%m%d"
            )
            spot_response = self._post(url=self._rate_url, request=request)

            try:
                spot_rates = self._format_response(
                    response=spot_response, service_code=self._spot_quote
                )
            except RateException as e:
                CeleryLogger().l_info.delay(
                    location="yrc_rate.py line: 305",
                    message=str({"api.error.yrc.rate": e.message}),
                )
                spot_rates = []

            if spot_rates:
                rates.append(spot_rates)

        return rates

    def rate(self) -> list:
        """
        Get rates for YRC
        :return: list of dictionary rates
        """

        # # Max packages of 10 for YRC
        # if len(self._ubbe_request["packages"]) > 10:
        #     connection.close()
        #     raise RateException(f"YRC Rate (L192): Over maximum packages of 10")

        if (
            self._ubbe_request["origin"]["province"] in self._north
            or self._ubbe_request["destination"]["province"] in self._north
        ):
            connection.close()
            # raise RateException(f"YRC Rate (L192): Invalid Canadian Province.")
            return []

        try:
            request = self._create_request()
        except RateException as e:
            connection.close()
            raise RateException(
                f"YRC Rate (L198): Failed building request. {e.message}"
            ) from e

        try:
            (
                time_critical_noon_request,
                time_critical_5_request,
            ) = self._create_request_time_critical(request=request)
        except RateException as e:
            connection.close()
            raise RateException(
                f"YRC Rate (L198): Failed building request. {e.message}"
            ) from e

        try:
            rates = self._get_rates(
                request=request,
                time_critical_noon_request=time_critical_noon_request,
                time_critical_5_request=time_critical_5_request,
            )
        except RequestError as e:
            connection.close()
            raise RateException(
                f"YRC Rate (L204): No Rates sending request {str(e)}."
            ) from e

        return rates
