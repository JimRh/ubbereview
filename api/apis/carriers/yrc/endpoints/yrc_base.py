"""
    Title: YRC Base api
    Description: This file will contain all functions to get yrc common functionality between the endpoints.
    Created: November 26, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import re
import string
from decimal import Decimal

import requests
from django.db import connection
from lxml import etree
from requests import Session
from zeep import Transport, CachingClient
from zeep.cache import InMemoryCache
from zeep.plugins import HistoryPlugin

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.carriers import YRC
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from brain.settings import YRC_REST_BASE_URL, DEBUG


class YRCBaseApi:
    """
    YRC Api Class
    """

    _carrier_name = "YRC Freight"
    _default_transit = 10
    _success = "0000"

    _hundred = Decimal("100.00")
    _sig_fig = Decimal("0.01")
    _zero = Decimal("0.0")

    _special_characters = chars = re.escape(string.punctuation)

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

    # YRC Values
    _std_service = "STD"
    _tcsa_service = "TCSA"
    _tcsp_service = "TCSP"
    _spot_quote = "SPOT"
    _quote_type = "QUOTE"
    _query_type = "MATRX"
    _payment_terms = "Prepaid"
    _business_role = "Third Party"
    _US = "US"
    _USA = "USA"

    _MX = "MX"
    _MEX = "MEX"

    _CA = "CA"
    _CAN = "CAN"

    # YRC option codes
    _yrc_power_tailgate_pickup = "LFTO"
    _yrc_power_tailgate_delivery = "LFTD"
    _yrc_inside_pickup = "IP"
    _yrc_inside_delivery = "ID"
    _yrc_residential_pickup = "HOMP"
    _yrc_residential_delivery = "HOMD"
    _yrc_delivery_appointment = "APPT"
    _yrc_protect_from_freezing = "FREZ"

    # YRC Services
    _service_spot = "SPOT VOLUME"
    _service_name_spot = "Standard SV"
    _services = {
        "STD": "Standard LTL",
        "TCSA": "Time Critical by noon",
        "TCSP": "Time Critical by 5 p.m.",
        "SPOT": "Standard SV",
    }

    _rate_to_pickup_services = {
        "STD": "LTL",
        "TCSA": "GTC",
        "TCSP": "GTC",
        "SPOT": "VOL",
    }

    _rate_to_ship_services = {"STD": "LTL", "TCSA": "GTC", "TCSP": "GTC", "SPOT": "LTL"}

    _guaranteed = "GD"

    package_type_map = {
        "BAG": "BAG",
        "BOX": "BOX",
        "CONTAINER": "CNT",
        "CRATE": "CRT",
        "DRUM": "DRM",
        "REEL": "REL",
        "ROLL": "ROL",
        "SKID": "SKD",
        "TUBE": "TBE",
    }

    pickup_package_type_map = {
        "SKID": "PLT",
        "DRUM": "DRM",
        "REEL": "REL",
        "ROLL": "ROL",
    }

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

    # YRC Urls
    _rate_url = f"{YRC_REST_BASE_URL}/node/api/ratequote"
    _pickup_url = f"{YRC_REST_BASE_URL}/node/api/pickup"

    # SOAP Values
    _history = None
    _client = None
    _name_space = None

    def __init__(self, ubbe_request: dict):
        self._ubbe_request = copy.deepcopy(ubbe_request)

        self._sub_account = self._ubbe_request["objects"]["sub_account"]
        self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][YRC][
            "account"
        ]
        self._carrier = self._ubbe_request["objects"]["carrier_accounts"][YRC][
            "carrier"
        ]

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    @staticmethod
    def _default_transport():
        """
        Create default transport and authenticate with user and password.
        :return:
        """
        session = Session()
        return TransportSoapenv(cache=InMemoryCache(), session=session)

    def _build_json_auth(self) -> dict:
        return {
            "username": self._carrier_account.username.decrypt(),
            "password": self._carrier_account.password.decrypt(),
            "busId": self._carrier_account.contract_number.decrypt(),
            "busRole": self._business_role,
            "paymentTerms": self._payment_terms,
        }

    def _build_soap_auth(self) -> dict:
        return {
            "Username": self._carrier_account.username.decrypt(),
            "Password": self._carrier_account.password.decrypt(),
        }

    def create_connection(self):
        """
        Create SOAP Connect to puro web services.
        :param wsdl_path: Project path
        :return:
        """

        if DEBUG:
            wsdl = (
                "http://mytest.yrc.com/myyrc-api/national/WebServices/YRCSecureBOL.wsdl"
            )
        else:
            wsdl = "http://my.yrc.com/myyrc-api/national/WebServices/YRCSecureBOL.wsdl"

        self._history = HistoryPlugin()
        self._client = CachingClient(
            wsdl, transport=self._default_transport(), plugins=[self._history]
        )

        self._client.set_ns_prefix("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self._client.set_ns_prefix("xsd", "http://www.w3.org/2001/XMLSchema")
        self._client.set_ns_prefix(
            "yrc",
            "http://my.yrc.com/national/WebServices/2009/01/31/YRCSecureBOL.wsdl",
        )
        self._client.set_ns_prefix("soap", "http://schemas.xmlsoap.org/soap/encoding/")

    def _post(self, url: str, request: dict):
        """
        Make YRC post api call.
        """

        try:
            response = requests.post(
                url=url, json=request, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(
                None, {"url": self._rate_url, "error": str(e), "data": request}
            ) from e

        try:
            response = response.json()
        except ValueError as e:
            CeleryLogger().l_critical.delay(
                location="yrc_base.py line: 116", message=f"{response.text}"
            )
            connection.close()
            raise RequestError(
                response, {"url": self._rate_url, "error": str(e), "data": request}
            ) from e

        connection.close()
        return response

    def _remove_special_characters(self, string_value: str) -> str:
        """
        Remove special characters from string.
        :param string_value:
        :return:
        """
        return re.sub(r"[" + self._special_characters + "]", " ", string_value)


class TransportSoapenv(Transport):
    """
    Transport SOAP ENV Modification
    """

    @staticmethod
    def replace_soapenv(envelope):
        """
        Modify Soap ENV into yrc format.
        :param envelope:
        :return:
        """
        message = etree.tostring(envelope)

        message = message.replace(b"soap-env:", b"soapenv:")
        message = message.replace(b"soap-env=", b"soapenv=")

        message = message.replace(
            b"<yrc:submitBOL",
            b'<yrc:submitBOL soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"',
        )

        message = message.replace(
            b"<commodityItem",
            b'<commodityItem xsi:type="yrc1:CommodityArray" soap:arrayType="yrc1:CommodityItem[]" xmlns:yrc1="http://my.yrc.com/national/WebServices/2009/01/31/YRCBoLTypes.xsd"',
        )

        message = message.replace(
            b"<serviceOptions",
            b'<serviceOptions xsi:type="yrc1:ServiceOptionsArray" soap:arrayType="yrc1:ServiceOption[]" xmlns:yrc1="http://my.yrc.com/national/WebServices/2009/01/31/YRCBoLTypes.xsd"',
        )

        message = message.replace(
            b"<referenceNumbers",
            b'<referenceNumbers xsi:type="yrc1:ReferenceNumberArray" soap:arrayType="yrc1:ReferenceNumber[]" xmlns:yrc1="http://my.yrc.com/national/WebServices/2009/01/31/YRCBoLTypes.xsd"',
        )

        return message

    def post_xml(self, address, envelope, headers):
        message = TransportSoapenv.replace_soapenv(envelope)
        return self.post(address, message, headers)
