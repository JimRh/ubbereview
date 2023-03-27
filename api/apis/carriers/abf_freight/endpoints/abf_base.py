"""
    Title: ABF Base api
    Description: This file will contain all functions to get abf common functionality between the endpoints.
    Created: June 26, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal
from typing import Union

import requests
import xmltodict
from django.db import connection

from api.apis.exchange_rate.exchange_rate import ExchangeRateUtility
from api.exceptions.project import RequestError
from api.globals.carriers import ABF_FREIGHT
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import CityNameAlias
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ABFFreightBaseApi:
    """
    YRC Api Class
    """

    _carrier_name = "ABF Freight"
    _carrier_currency = "USD"
    _time_critical_service_codes = ["1200", "1700"]
    _default_transit = 10

    _hundred = Decimal("100.00")
    _sig_fig = Decimal("0.01")
    _sig_fig_weight = Decimal("0")
    _zero = Decimal("0.0")

    _cache_expiry = TWENTY_FOUR_HOURS_CACHE_TTL * 6

    # ubbe option codes
    _delivery_appointment = 1
    _pickup_appointment = 2
    _tailgate = 3
    _heated_truck = 6
    _refrigerated_truck = 5
    _power_tailgate_pickup = 3
    _power_tailgate_delivery = 17
    _inside_pickup = 9
    _inside_delivery = 10

    # ABF Freight class to ubbe Relation
    _freight_class_map = {
        "50.00": 50,
        "55.00": 55,
        "60.00": 60,
        "65.00": 65,
        "70.00": 70,
        "77.50": 77.5,
        "85.00": 85,
        "92.50": 92.5,
        "100.00": 100,
        "110.00": 110,
        "125.00": 125,
        "150.00": 150,
        "175.00": 175,
        "200.00": 200,
        "250.00": 250,
        "300.00": 300,
        "400.00": 400,
        "500.00": 500,
    }

    _package_type_map = {
        "A": "BAG",
        "B": "BL",
        "C": "BRL",
        "D": "BSK",
        "E": "BX",
        "F": "BKT",
        "G": "BLKH",
        "BUNDLES": "BDL",
        "H": "CRB",
        "I": "CTN",
        "J": "CS",
        "K": "CHT",
        "L": "CL",
        "CRATE": "CRT",
        "M": "CYL",
        "DRUM": "DR",
        "N": "FIR",
        "Q": "HMP",
        "R": "HHD",
        "S": "KEG",
        "BOX": "PKG",
        "PAIL": "PL",
        "T": "PLT",
        "U": "PC",
        "V": "RK",
        "REEL": "REL",
        "ROLL": "RL",
        "SKID": "SKD",
        "X": "SLP",
        "TOTES": "TOTE",
        "Y": "TRK",
        "TUBE": "TB",
    }

    _north = ["NT", "NU", "YT"]

    # ABF Freight Urls
    _rate_url = "https://www.abfs.com/xml/aquotexml.asp"
    _spot_rate_url = "https://api.arcb.com/quotes/volume/xml/"

    _ship_url = "https://www.abfs.com/xml/bolxml.asp"
    _pickup_url = "https://www.abfs.com/xml/pickupxml.asp"

    def __init__(self, ubbe_request: dict):
        self._ubbe_request = copy.deepcopy(ubbe_request)

        self._sub_account = self._ubbe_request["objects"]["sub_account"]
        self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
            ABF_FREIGHT
        ]["account"]
        self._carrier = self._ubbe_request["objects"]["carrier_accounts"][ABF_FREIGHT][
            "carrier"
        ]

        self._api_key = self._carrier_account.api_key.decrypt()
        self._account_number = self._carrier_account.account_number.decrypt()

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    @staticmethod
    def _build_address(key: str, address: dict, is_full: bool = False) -> {}:
        """
        Build ABF Address layout for shipper and consignee.
        :param key: address type
        :param address: Origin or Destination address dictionary
        :param is_full: Create Full Address
        :return: ABF Address dict
        """

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=ABF_FREIGHT,
        )

        ret = {
            f"{key}City": city,
            f"{key}State": address["province"],
            f"{key}Country": address["country"],
            f"{key}Zip": address["postal_code"],
        }

        if is_full:
            ret.update(
                {
                    f"{key}Name": address["company_name"],
                    f"{key}Contact": address["name"],
                    f"{key}NamePlus": address["name"],
                    f"{key}Phone": address["phone"],
                    f"{key}Email": "customerservice@ubbe.com",
                    f"{key}Address": address["address"],
                }
            )

        return ret

    @staticmethod
    def _build_requester_information() -> {}:
        """
        Build ABF Requester Information.
        :return: ABF Third Party dict
        """

        return {
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
        }

    @staticmethod
    def _get(
        url: str, params: dict = None, rate_type: str = "", headers: dict = None
    ) -> Union[list, dict]:
        """
        Make ABF Freight get api call.
        """

        if not params:
            params = {}

        try:
            response = requests.get(
                url=url, timeout=DEFAULT_TIMEOUT_SECONDS, headers=headers, params=params
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": url, "error": str(e)}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": url})

        try:
            converted_xml = xmltodict.parse(xml_input=response.content)
        except KeyError as e:
            raise RequestError(response, {"url": url, "error": str(e)}) from e

        return {"is_error": False, "response": converted_xml, "rate_type": rate_type}

    @staticmethod
    def _get_content(url: str, params: dict = None, headers: dict = None) -> bytes:
        """
        Make ABF Freight get api call to download documents.
        """

        if not params:
            params = {}

        try:
            response = requests.get(
                url=url, timeout=DEFAULT_TIMEOUT_SECONDS, headers=headers, params=params
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(None, {"url": url, "error": str(e)}) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": url})

        return response.content

    def _build_options(self, options: []) -> dict:
        """
        Build ABF Option Details from ubbe options.
        :return: ABF Option Dictionary
        """

        ret = {}

        if not self._ubbe_request["origin"].get("has_shipping_bays", True):
            ret["Acc_RPU"] = "Y"

        if not self._ubbe_request["destination"].get("has_shipping_bays", True):
            ret["Acc_RDEL"] = "Y"

        if self._ubbe_request.get("is_dangerous_goods", False):
            ret["Acc_HAZ"] = "Y"

        if not options:
            return ret

        for option in options:
            if option == self._inside_pickup:
                ret["Acc_IPU"] = "Y"
            elif option == self._inside_delivery:
                ret["Acc_IDEL"] = "Y"
            elif option == self._power_tailgate_pickup:
                ret["Acc_GRD_PU"] = "Y"
            elif option == self._power_tailgate_delivery:
                ret["Acc_GRD_DEL"] = "Y"
            elif option == self._heated_truck:
                ret["Acc_FRE"] = "Y"

        return ret

    def _build_reference_numbers(self) -> {}:
        """
        Build ABF Reference Numbers.
        :return: ABF Reference Numbers dict
        """
        return {
            "Bol": self._ubbe_request["order_number"],
            "PO1": self._ubbe_request.get("reference_one", "")[:20],
            "PO2": self._ubbe_request.get("reference_two", "")[:20],
        }

    def _build_third_party(self) -> {}:
        """
        Build ABF Third Party.
        :return: ABF Third Party dict
        """
        tp = {
            "company_name": "BBE Expediting",
            "name": "Customer Service",
            "phone": "18884206926",
            "address": "1759 35 Ave E",
            "city": "Edmonton International Airport",
            "province": "AB",
            "country": "CA",
            "postal_code": "T9E0V6",
        }

        return self._build_address(key="TPB", address=tp, is_full=True)

    def _apply_exchange_rate(self, rate: dict, is_ship: bool = False):
        """

        :param rate:
        :param is_ship:
        :return:
        """

        from_exchange_rate = ExchangeRateUtility(
            source_currency=self._carrier_currency, target_currency="CAD"
        ).get_exchange_rate()

        to_exchange_rate = ExchangeRateUtility(
            source_currency="CAD", target_currency=self._carrier_currency
        ).get_exchange_rate()

        rate.update(
            {
                "freight": (rate["freight"] * from_exchange_rate).quantize(
                    self._sig_fig
                ),
                "total": (rate["total"] * from_exchange_rate).quantize(self._sig_fig),
                "exchange_rate": {
                    "from_source": from_exchange_rate,
                    "to_source": to_exchange_rate,
                    "from_currency": self._carrier_currency,
                    "to_currency": "CAD",
                },
            }
        )

        if is_ship:
            rate["surcharges_cost"] = (
                rate["surcharges_cost"] * from_exchange_rate
            ).quantize(self._sig_fig)
            rate["taxes"] = (rate["taxes"] * from_exchange_rate).quantize(self._sig_fig)
        else:
            rate["surcharge"] = (rate["surcharge"] * from_exchange_rate).quantize(
                self._sig_fig
            )
            rate["tax"] = (rate["tax"] * from_exchange_rate).quantize(self._sig_fig)
