"""
    Title: Manitoulin Ship api
    Description: This file will contain functions related to Manitoulin Ship Api.
    Created:  December, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal, ROUND_UP

from django.core.cache import cache
from django.db import connection

from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi
from api.apis.carriers.manitoulin.endpoints.manitoulin_document import (
    ManitoulinDocument,
)
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException, RequestError
from api.globals.carriers import MANITOULIN
from api.models import CityNameAlias


class ManitoulinShip(ManitoulinBaseApi):
    """
    Manitoulin Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._response = {}

        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]

    def _build_address(self, key: str, address: dict) -> {}:
        """
        Build Manitoulin Address layout for shipper and consignee.
        :param key: address type
        :param address: Origin or Destination address dictionary
        :return: Manitoulin Address dict
        """
        country = address["country"]

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=country,
            carrier_id=MANITOULIN,
        )

        if country == "CA":
            country = "CN"

        ret = {
            f"{key}CODE": self._account_number,
            f"{key}NAME": address["company_name"],
            f"{key}ADDR": address["address"],
            f"{key}CITY": city,
            f"{key}PROV": address["province"],
            f"{key}PC": address["postal_code"],
            f"{key}NAT": country,
        }

        return ret

    def _build_options(self) -> dict:
        """
        Build Manitoulin Option Details from ubbe options.
        :return: Manitoulin Option Dictionary
        """
        ret = {
            "OTYPE": "BWLD",
            "OPICKUP": "NONE",
            "DTYPE": "BWLD",
            "DDEL": "NONE",
            "HEAT": False,
            "FRESH": False,
            "FROZEN": False,
            "FDPU": False,
            "FDDEL": False,
            "WP": False,
            "WD": False,
        }

        if not self._ubbe_request["origin"].get("has_shipping_bays", True):
            ret["OTYPE"] = "RRWOLD"

        if not self._ubbe_request["destination"].get("has_shipping_bays", True):
            ret["DTYPE"] = "RRWOLD"

        for option in self._ubbe_request.get("carrier_options", []):
            if option == self._heated_truck:
                ret["HEAT"] = True
            elif option == self._refrigerated_truck:
                ret["FRESH"] = True
            elif option == self._delivery_appointment:
                ret["APPTDEL"] = True
        return ret

    def _build_details(self):
        """
        Build Manitoulin Packages from ubbe packages.
        :return: dictionary of Manitoulin Packages
        """
        package_list = []
        count = 1

        for package in self._ubbe_request["packages"]:
            ret = {
                "BOL_ID": f'{self._ubbe_request["order_number"]}-{count}',
                "CLASS": self._freight_class_map[package.get("freight_class", "70.00")],
                "PKGCODE": self._quote_package_type_map[package["package_type"]],
                "NUMPCS": package["quantity"],
                "DESC": package["description"],
                "WEIGHT": int(
                    package["imperial_weight"].quantize(Decimal("1"), rounding=ROUND_UP)
                ),
                "LENGTH": int(
                    package["imperial_length"].quantize(Decimal("1"), rounding=ROUND_UP)
                ),
                "HEIGHT": int(
                    package["imperial_height"].quantize(Decimal("1"), rounding=ROUND_UP)
                ),
                "WIDTH": int(
                    package["imperial_width"].quantize(Decimal("1"), rounding=ROUND_UP)
                ),
                "WGTUNITS": "LBS",
                "DIMUNITS": "IN",
                "DG": False,
                "DGUN": None,
                "DGNAME": None,
                "DGPG": None,
                "DGCLASS": None,
                "COMMENTS": "",
                "DGTECHNM": "",
            }

            if package["is_dangerous_good"]:
                ret.update(
                    {
                        "DG": True,
                        "DGUN": package["un_number"],
                        "DGNAME": package["proper_shipping_name"],
                        "DGPG": package["packing_group_str"],
                        "DGCLASS": package["class_div"],
                    }
                )

            package_list.append(ret)
            count += 1

        return package_list

    def _get_pickup_date(self) -> str:
        """
        Gets pickup date from ubbe request or uses the current date/time
        :return: pickup date
        """
        pickup_date = None

        if self._ubbe_request["is_pickup"]:
            pickup_date = self._ubbe_request["pickup"]["date"]

        if not pickup_date:
            pickup_date = datetime.datetime.now() + datetime.timedelta(days=1)

        return pickup_date.strftime("%Y%m%d")

    def _build_request(self) -> dict:
        """
        Build Manitoulin Ship request Dictionary
        :return: Manitoulin Ship Request Dictionary
        """
        service_parts = self._ubbe_request["service_code"].split("|")
        service_code = service_parts[0]
        quote_id = service_parts[1]

        ret = {
            "SCB": "B",
            "TERMS": "T",
            "PUDATE": self._get_pickup_date(),
            "GS": self._ship_service_codes[service_code],
            "BILLCODE": self._account_number,
            "BILLNAME": "BBE Expediting Ltd",
            "BILLADDR": "1759 35 Ave E",
            "BILLCITY": "Edmonton International Airport",
            "BILLPROV": "AB",
            "BILLPC": "T9E0V6",
            "BILLNAT": "CN",
            "STYPE": "LTL Expedited",
            "CONTNAME": "Customer Service",
            "CONTPHONE": "18884206926",
            "PERSONAL": False,
            "ARCHIVED": False,
            "PRONUM": "",
            "BOLNUM": self._ubbe_request["order_number"],
            "PONUM": self._ubbe_request["order_number"],
            "ORDERNUM": self._ubbe_request["order_number"],
            "REFNUM": f"{self._ubbe_request.get('reference_one', '')[:25]}",
            "SHIPNUM": self._ubbe_request.get("reference_two", "")[:25],
            "INSTRUCT": self._ubbe_request.get("special_instructions", "")[:300],
            "TRACKNUM": "",
            "QTENUM": quote_id,
            "DECVAL": None,
            "DECVALC": "C",
            "NOTIFY": False,
            "NOTNAME": "",
            "NOTPHONE": "",
            "APPTDEL": False,
            "APPTDATE": None,
            "APPTTIMETYPE": "",
            "APPTTIMESTART": None,
            "APPTTIMEEND": None,
            "EMERGNAME": "",
            "EMERGPHONE": "",
            "ERAPNUMBER": "",
            "ERAPPHONE": "",
            "CARROUT": "",
            "TRANSPOINT": "",
            "PICKUPNUM": "",
            "OFFHOURPU": False,
            "OFFHOURDEL": False,
            "ORIGPRONUM": "",
            "ORIGTERM": None,
            "DESTTERM": None,
            "TMPNAME": "",
        }

        ret.update(self._build_address(key="SHIP", address=self._origin))
        ret.update(self._build_address(key="CONS", address=self._destination))
        ret.update(self._build_options())
        ret.update({"DETAILS": self._build_details()})

        return ret

    def _format_response(self, response: dict) -> dict:
        """
        Formats response from manitoulin api endpoint into ubbe format
        :param response:
        :return: dict containing data from mantioulin endpoint in ubbe format
        """

        service_parts = self._ubbe_request["service_code"].split("|")
        service_code = service_parts[0]
        quote_id = service_parts[1]
        cached_rate = cache.get(f"{MANITOULIN}-{quote_id}-{service_code}")

        if not cached_rate:
            raise ShipException("Manitoulin Ship (L230): Error with Cached Rate.")

        cache.delete_pattern(f"{MANITOULIN}-{quote_id}*")

        # TODO - Fallback to BBE documents or straight fail?
        documents = ManitoulinDocument(ubbe_request=self._ubbe_request).get_documents(
            bol_id=response["bol_id"]
        )

        ret = {
            "carrier_id": MANITOULIN,
            "carrier_name": self._carrier_name,
            "service_code": service_code,
            "service_name": self._services[service_code],
            "freight": cached_rate["freight"],
            "surcharges": cached_rate["surcharge_list"],
            "surcharges_cost": cached_rate["surcharge"],
            "tax_percent": cached_rate["tax_percent"],
            "taxes": cached_rate["tax"],
            "total": cached_rate["total"],
            "tracking_number": response["probill_number"],
            "pickup_id": "",
            "transit_days": cached_rate["transit_days"],
            "delivery_date": cached_rate["delivery_date"],
            "carrier_api_id": quote_id,
            "documents": documents,
        }

        return ret

    def ship(self) -> dict:
        """
        Ship Manitoulin shipment.
        :return: ubbe format response
        """

        if self._origin["province"] == "NU" or self._destination["province"] == "NU":
            connection.close()
            raise ShipException("TST-CF Rate (L187): Not Supported Region.")

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise ShipException(f"Manitoulin Ship (L286): {str(e)}") from e

        try:
            response = self._post(url=self._ship_url, request=request)
        except RequestError as e:
            connection.close()
            raise ShipException(f"Manitoulin Ship (L292): {str(e)}") from e

        if not response.get("bol_id") and not response.get("probill_number"):
            connection.close()
            raise ShipException(f"Manitoulin Ship (L292): {str(response)}")

        try:
            response = self._format_response(response=response)
        except ShipException as e:
            CeleryLogger.l_critical(
                location="manitoulin_api.py",
                message=str(e),
            )
            connection.close()
            raise ShipException(
                f"Manitoulin Ship (L298): {str(e.message)}\n{response}\n{request}"
            ) from e
        except Exception as e:
            CeleryLogger.l_critical(
                location="manitoulin_api.py",
                message=str(e),
            )
            connection.close()
            raise ShipException(
                f"Manitoulin Ship (L301): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return response
