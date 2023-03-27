"""
    Title: ABF Freight Rate api
    Description: This file will contain functions related to ABF Freight rate Api.
    Created: June 23, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

import gevent
from django.core.cache import cache
from django.db import connection

from api.apis.carriers.abf_freight.endpoints.abf_base import ABFFreightBaseApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RateException, RequestError
from api.globals.carriers import ABF_FREIGHT
from api.utilities.date_utility import DateUtility


class ABFRate(ABFFreightBaseApi):
    """
    ABF Freight Rate Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._request = {}
        self._response = []

    def _build_packages(self) -> dict:
        """
        Build ABF Packages from ubbe packages.
        :return: dictionary of ABF Packages
        """
        ret = {"FrtLWHType": "IN"}
        count = 1

        for package in self._ubbe_request["packages"]:
            ret.update(
                {
                    f"Desc{count}": package["description"],
                    f"UnitNo{count}": package["quantity"],
                    f"UnitType{count}": self._package_type_map[package["package_type"]],
                    f"Class{count}": self._freight_class_map[package["freight_class"]],
                    f"FrtLng{count}": package["imperial_length"],
                    f"FrtWdth{count}": package["imperial_width"],
                    f"FrtHght{count}": package["imperial_height"],
                    f"Wgt{count}": Decimal(
                        package["imperial_weight"] * package["quantity"]
                    ).quantize(self._sig_fig_weight),
                }
            )

            count += 1

        return ret

    def _build_pickup(self) -> dict:
        """
        Build ABF Pickup Details from ubbe pickup if exists, otherwise use today.
        :return: ABF Pickup Dictionary
        """

        if "pickup" in self._ubbe_request:
            pickup_date = self._ubbe_request["pickup"]["date"]
        else:
            pickup_date = datetime.datetime.today().date()

        return {
            "ShipMonth": pickup_date.month,
            "ShipDay": pickup_date.day,
            "ShipYear": pickup_date.year,
        }

    def _build_third_party(self) -> dict:
        """
        Build ABF Third Party.
        :return: ABF Third Party dict
        """

        return {
            "TPBAff": "Y",
            "TPBPay": "Y",
            "TPBName": "BBE Expediting",
            "TPBAddr": "1759 35 Ave E",
            "TPBCity": "Edmonton Intl Airport",
            "TPBState": "AB",
            "TPBZip": "T9E0V6",
            "TPBCountry": "CA",
            "TPBAcct": self._account_number,
        }

    def _build_request(self) -> dict:
        """
        Build ABF rate request Dictionary
        :return: ABF Rate Request Dictionary
        """

        ret = {
            "ID": self._api_key,
        }

        ret.update(
            self._build_address(key="Ship", address=self._ubbe_request["origin"])
        )
        ret.update(
            self._build_address(key="Cons", address=self._ubbe_request["destination"])
        )
        ret.update(self._build_third_party())
        ret.update(self._build_packages())
        ret.update(self._build_pickup())
        ret.update(
            self._build_options(options=self._ubbe_request.get("carrier_options", []))
        )

        return ret

    def _format_ca_price(self, data: dict) -> dict:
        """
        Format Rate Response into ubbe format
        :param data: Response Data
        :return: list of ubbe format rates
        """
        surcharges = []

        freight = Decimal("0.0")
        surcharge_cost = Decimal("0.0")
        tax = Decimal("0.0")
        total = Decimal(data["CHARGE"]).quantize(self._sig_fig)
        tax_percent = Decimal("0.0")

        for item in data["ITEMIZEDCHARGES"]["ITEM"]:
            description = item["@DESCRIPTION"]
            item_type = item["@FOR"]
            amount = Decimal(item["@AMOUNT"]).quantize(self._sig_fig)

            if item_type in ["SS", "RESO", "RESD", "IPU", "IDEL", "GRP", "GRD", "HAZ"]:
                surcharges.append(
                    {"name": description, "cost": amount, "percentage": Decimal("0.0")}
                )
                surcharge_cost += amount
            elif item_type == "FSC":
                fsc = Decimal(item["@RATE"].replace("%", ""))
                surcharges.append(
                    {"name": description, "cost": amount, "percentage": fsc}
                )
                surcharge_cost += amount
            elif item_type in ["GST", "HST", "QST", "PST", "RST"]:
                tax_percent = Decimal(item["@RATE"].replace("%", ""))
                tax = amount
                surcharges.append(
                    {"name": description, "cost": tax, "percentage": tax_percent}
                )
            elif item_type == "FREIGHT":
                freight = amount
            else:
                surcharges.append(
                    {"name": description, "cost": amount, "percentage": Decimal("0.0")}
                )
                surcharge_cost += amount

        ret = {
            "freight": freight,
            "surcharge": surcharge_cost,
            "surcharge_list": surcharges,
            "tax": tax,
            "tax_percent": tax_percent,
            "total": total,
        }

        return ret

    def _format_other_price(self, data: dict) -> dict:
        pass

    def _format_response(self, response: dict, rate_type: str) -> list:
        """
        Format ABF Freight Quote Api Response
        :return: ubbe Format.
        """
        rates = []

        if not response:
            return rates

        rate_key = "ABF" if rate_type == "NORMAL" else "ARCBEST"

        if not response[rate_key]:
            return rates

        response = response[rate_key]

        if int(response["NUMERRORS"]) > 0:
            message = str({"abf_rate": f"ABF Failure: {str(response['ERROR'])}"})
            CeleryLogger().l_critical.delay(
                location="abf_rate.py line: 206", message=message
            )
            return rates

        transit_key = (
            "ADVERTISEDTRANSIT" if rate_type == "NORMAL" else "ESTIMATEDTRANSIT"
        )
        est_date_key = "ADVERTISEDDUEDATE" if rate_type == "NORMAL" else ""
        service_name = "LTL" if rate_type == "NORMAL" else "Spot LTL"
        service_code = "LTL" if rate_type == "NORMAL" else "SV"
        charges = Decimal(response["CHARGE"]).quantize(self._sig_fig)

        try:
            transit = int(
                response.get(transit_key, self._default_transit)
                .replace(" ", "")
                .replace("Days", "")
            )
        except Exception:
            transit = self._default_transit

        try:
            est_delivery_date = datetime.datetime.strptime(
                response[est_date_key], "%Y-%m-%d"
            )
            estimated_delivery_date = est_delivery_date.isoformat()
        except Exception:
            estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
                transit=transit,
                country=self._ubbe_request["origin"]["country"],
                province=self._ubbe_request["origin"]["province"],
            )

        rate_ltl = {
            "carrier_id": ABF_FREIGHT,
            "carrier_name": self._carrier_name,
            "service_code": f'{service_code}|{response["QUOTEID"]}',
            "service_name": f"{service_name}",
            "freight": charges.quantize(self._sig_fig),
            "surcharge": Decimal("0.00").quantize(self._sig_fig),
            "surcharge_list": [],
            "tax": Decimal("0.00").quantize(self._sig_fig),
            "tax_percent": "0",
            "total": charges.quantize(self._sig_fig),
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
        }

        if (
            self._ubbe_request["origin"]["country"] == "CA"
            and self._ubbe_request["destination"]["country"] == "CA"
        ):
            rate_ltl.update(self._format_ca_price(data=response))

        cache.set(rate_ltl["service_code"], rate_ltl, self._cache_expiry)
        del rate_ltl["surcharge_list"]
        rates.append(rate_ltl)

        if (
            "GUARANTEEDOPTIONS" in response
            and int(response["GUARANTEEDOPTIONS"]["NUMOPTIONS"]) > 0
        ):
            for option in response["GUARANTEEDOPTIONS"]["OPTION"]:
                copied = copy.deepcopy(rate_ltl)
                g_charges = Decimal(option["GUARANTEEDCHARGE"]).quantize(self._sig_fig)

                copied.update(
                    {
                        "service_code": f"{option['GUARANTEEDBYTIME']}|{response['QUOTEID']}",
                        "service_name": f"Guaranteed {option['GUARANTEEDBYTIME']}",
                        "freight": g_charges.quantize(self._sig_fig),
                        "surcharge": Decimal("0.00").quantize(self._sig_fig),
                        "surcharge_list": [],
                        "tax": Decimal("0.00").quantize(self._sig_fig),
                        "tax_percent": "0",
                        "total": g_charges.quantize(self._sig_fig),
                    }
                )

                if (
                    self._ubbe_request["origin"]["country"] == "CA"
                    and self._ubbe_request["destination"]["country"] == "CA"
                ):
                    g_sub_total = g_charges / (
                        (Decimal(rate_ltl["tax_percent"]) / Decimal("100")) + 1
                    )
                    g_tax = g_charges - g_sub_total

                    copied["freight"] = g_sub_total.quantize(self._sig_fig)
                    copied["tax"] = g_tax.quantize(self._sig_fig)
                    copied["tax_percent"] = Decimal(rate_ltl["tax_percent"])
                    copied["total"] = g_charges.quantize(self._sig_fig)

                rates.append(copied)
                cache.set(copied["service_code"], copied, self._cache_expiry)

        return rates

    def _get_rates(self, requests: []) -> list:
        """
        Get ABF Rates
        :param requests: List of Requests
        :return:
        """
        send_list = []
        response_rates = []

        for request in requests:
            send_list.append(
                gevent.Greenlet.spawn(
                    self._get, request["url"], request["request"], request["rate_type"]
                )
            )

        gevent.joinall(send_list)

        for request in send_list:
            try:
                response = request.get()
            except Exception:
                response = {"is_error": True, "response": {}, "rate_type": "FAIL"}

            if response["is_error"]:
                continue

            try:
                rates = self._format_response(
                    response=response["response"], rate_type=response["rate_type"]
                )
            except RateException as e:
                message = str(
                    f"ABF Freight Rate (L198): Failed building request. {e.message}"
                )
                CeleryLogger().l_critical.delay(
                    location="abf_rate.py line: 206", message=message
                )
                continue

            response_rates.extend(rates)

        for rate in response_rates:
            self._apply_exchange_rate(rate=rate)

        return response_rates

    def rate(self) -> list:
        """
        Get rates for ABF Freight
        :return: list of dictionary rates
        """
        requests = []

        if self._ubbe_request["origin"]["country"] not in [
            "CA",
            "US",
            "MX",
        ] or self._ubbe_request["destination"]["country"] not in ["CA", "US", "MX"]:
            connection.close()
            return []

        if (
            self._ubbe_request["origin"]["province"] in self._north
            or self._ubbe_request["destination"]["province"] in self._north
        ):
            connection.close()
            return []

        try:
            request = self._build_request()
        except RateException as e:
            connection.close()
            raise RateException(
                f"ABF Freight Rate (L198): Failed building request. {e.message}"
            ) from e

        if self._ubbe_request["total_weight_imperial"] < 15000:
            requests.append(
                {"request": request, "url": self._rate_url, "rate_type": "NORMAL"}
            )

        if self._ubbe_request["total_weight_imperial"] >= 5000:
            spot_request = copy.deepcopy(request)

            spot_request.update(
                {
                    "RequesterName": "BBE Expediting Ltd.",
                    "RequesterEmail": "customerservice@ubbe.com",
                }
            )

            requests.append(
                {
                    "request": spot_request,
                    "url": self._spot_rate_url,
                    "rate_type": "SPOT",
                }
            )

        if not request:
            connection.close()
            return []

        try:
            rates = self._get_rates(requests=requests)
        except RequestError as e:
            connection.close()
            raise RateException(
                f"ABF Freight Rate (L204): No Rates sending request {str(e)}."
            ) from e

        return rates
