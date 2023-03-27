"""
    Title: TST CF Express Api V2
    Description: This file will contain common functionality related to TST CF Express Base Api V2.
    Created: Jan 16,, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
import requests
import xmltodict
from django.db import connection
from lxml import etree

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.carriers import TST
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from brain.settings import DEBUG


class TstCfExpressApi:
    """
    TST CF Express Base Api Class
    """

    _carrier_name = "TST-CF Express"
    _road_service = "ST"
    _g1_service = "G1"
    _g2_service = "G2"
    _g3_service = "G3"
    _services = [
        "ST",
        "G1",
        "G2",
        "G3",
    ]

    _services_names = {
        "ST": "Road",
        "G1": "TST-CF Guaranteed 5PM",
        "G2": "TST-CF Guaranteed 9AM",
        "G3": "TST-CF Guaranteed noon",
    }

    _freight_classes = {
        "50.00": "050",
        "55.00": "055",
        "60.00": "065",
        "65.00": "065",
        "70.00": "070",
        "77.50": "077",
        "85.00": "085",
        "92.50": "092",
        "100.00": "100",
        "110.00": "110",
        "125.00": "125",
        "150.00": "150",
        "175.00": "175",
        "200.00": "200",
        "250.00": "250",
        "300.00": "300",
        "400.00": "400",
        "500.00": "500",
    }

    _package_codes = {
        "BAG": "BAG",
        "BOX": "BOX",
        "BUNDLES": "BDL",
        "CRATE": "CRT",
        "DRUM": "DRM",
        "PAIL": "PLS",
        "REEL": "REL",
        "ROLL": "ROL",
        "SKID": "SKD",
        "TOTES": "TOT",
    }

    _north = ["NU", "NT", "YT"]

    # TST CF Express Endpoints
    _url = "https://www.tst-cfexpress.com/xml/"
    _rate_url = f"{_url}rate-quote"
    _ship_url = f"{_url}bol-pickup"
    _pickup_url = f"{_url}pickup"
    _bol_url = f"{_url}pro-assignment"
    _image_url = f"{_url}image"
    _track_url = f"{_url}tracing"

    # ubbe Options
    _delivery_appointment = 1
    _pickup_appointment = 2
    _tailgate = 3
    _heated_truck = 6
    _refrigerated_truck = 5
    _power_tailgate_pickup = 3
    _power_tailgate_delivery = 17
    _inside_pickup = 9
    _inside_delivery = 10

    def __init__(self, ubbe_request: dict):
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._is_test = DEBUG
        self._sub_account = self._ubbe_request["objects"]["sub_account"]
        self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][TST][
            "account"
        ]

        self._requestor = self._carrier_account.contract_number.decrypt()
        self._key = self._carrier_account.api_key.decrypt()
        self._login = self._carrier_account.username.decrypt()
        self._password = self._carrier_account.password.decrypt()

        copied = copy.deepcopy(self._ubbe_request)

        if "dg_service" in copied:
            del copied["dg_service"]

        if "objects" in copied:
            del copied["objects"]

        self._error_world_request = copied

    @staticmethod
    def _add_child(element: str, value):
        """
        Create Child element for tst request from element name and value.
        :param element: Element Name
        :param value: Value for Element
        :return: Child Element
        """
        child = etree.Element(element)
        child.text = value
        return child

    @staticmethod
    def _format_values(data):
        try:
            transit_days = int(str(data["transitresults"]["servicedays"]))
            transit_days += 1
        except Exception:
            transit_days = -1

        try:
            date = str(data["transitresults"]["arrivaldate"])
            delivery_date = datetime.datetime.strptime(date, "%Y%m%d")
        except Exception:
            delivery_date = datetime.datetime.now().replace(
                microsecond=0, second=0, minute=0, hour=0
            )

        if not delivery_date and transit_days:
            if transit_days != -1:
                estimated_delivery_date = (
                    datetime.datetime.utcnow()
                    + datetime.timedelta(days=int(transit_days))
                )
            else:
                estimated_delivery_date = datetime.datetime(year=1, month=1, day=1)

            delivery_date = estimated_delivery_date.replace(microsecond=0)

        return transit_days, delivery_date.isoformat()

    @staticmethod
    def _post(url: str, return_key: str, request) -> dict:
        """
        Make TST Post call for url and request.
        :param url: endpoint url.
        :param request: data for request.
        :return: TST response
        """
        data = etree.tostring(request, pretty_print=True).decode("ascii")

        try:
            response = requests.post(url, data=data, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException as e:
            connection.close()
            CeleryLogger().l_info.delay(
                location="tst_rate.py line: 344",
                message=f"TST Post: Post: {data} Error: {str(e)}",
            )
            raise RequestError(None, {}) from e

        # Check for request status
        if not response.ok:
            connection.close()
            CeleryLogger().l_info.delay(
                location="tst_rate.py line: 344",
                message=f"TST Post: Post: {data} Error: {str(response.text[:200])}",
            )
            raise RequestError(response, {})

        try:
            converted_xml = xmltodict.parse(xml_input=response.content)
            ret = converted_xml[return_key]
        except KeyError as e:
            raise RequestError(response, {}) from e

        if "errorcode" in ret:
            connection.close()
            CeleryLogger().l_info.delay(
                location="tst_rate.py line: 366",
                message=f"TST Rate return data: {data} - {response.text[:200]}",
            )
            raise RequestError(response, {})

        return ret

    def _add_auth(self, request) -> None:
        """
        Add Auth information to request.
        :param request: TST Request
        :return: None
        """
        request.append(self._add_child(element="requestor", value=self._requestor))
        request.append(self._add_child(element="authorization", value=self._key))
        request.append(self._add_child(element="login", value=self._login))
        request.append(self._add_child(element="passwd", value=self._password))

    def _build_options(self) -> etree.Element:
        """
        Add the corresponding options for the tst
        :return: option lxml object
        """
        options = etree.Element("accitems")

        for option in self._ubbe_request["carrier_options"]:
            # Appointment
            if option in (self._delivery_appointment, self._pickup_appointment):
                options.append(self._add_child(element="item", value="APT"))
            elif option == self._inside_pickup:
                options.append(self._add_child(element="item", value="INSPU"))
            elif option == self._inside_delivery:
                options.append(self._add_child(element="item", value="INSD"))
            elif option == self._heated_truck:
                options.append(self._add_child(element="item", value="HEAT"))
            elif option == self._refrigerated_truck:
                options.append(self._add_child(element="item", value="PSC"))
            elif option == self._power_tailgate_pickup:
                options.append(self._add_child(element="item", value="TGPU"))
            elif option == self._power_tailgate_delivery:
                options.append(self._add_child(element="item", value="TGDL"))

        if not self._ubbe_request["origin"].get("has_shipping_bays", True):
            options.append(self._add_child(element="item", value="PRP"))

        if not self._ubbe_request["destination"].get("has_shipping_bays", True):
            options.append(self._add_child(element="item", value="PRD"))

        return options
