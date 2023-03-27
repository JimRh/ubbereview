"""
    Title: ABF Ship api
    Description: This file will contain functions related to ABF Ship Api.
    Created:  June 27, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
import datetime
from decimal import Decimal

from django.core.cache import cache
from django.db import connection

from api.apis.carriers.abf_freight.endpoints.abf_base import ABFFreightBaseApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException, RequestError
from api.globals.carriers import ABF_FREIGHT
from api.globals.project import (
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_SHIPPING_LABEL,
)
from brain import settings


class ABFShip(ABFFreightBaseApi):
    """
    ABF Freight Ship Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._response = {}

        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._service_parts = self._ubbe_request["service_code"].split("|")

    @staticmethod
    def _build_document_settings() -> dict:
        """
        Build ABF Document Settings.
        :return: ABF Document Settings dict
        """
        return {
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
        }

    def _build_packages(self) -> dict:
        """
        Build ABF Packages from ubbe packages.
        :return: dictionary of ABF Packages
        """
        ret = {"LWHType": "IN"}
        count = 1

        for package in self._ubbe_request["packages"]:
            ret.update(
                {
                    f"HN{count}": package["quantity"],
                    f"HT{count}": self._package_type_map[package["package_type"]],
                    f"Desc{count}": package["description"],
                    f"PN{count}": package["quantity"],
                    f"PT{count}": self._package_type_map[package["package_type"]],
                    f"FrtLng{count}": package["imperial_length"],
                    f"FrtWdth{count}": package["imperial_width"],
                    f"FrtHght{count}": package["imperial_height"],
                    f"WT{count}": Decimal(
                        package["imperial_weight"] * package["quantity"]
                    ).quantize(self._sig_fig_weight),
                    f"CL{count}": self._freight_class_map[package["freight_class"]],
                }
            )

            if package["is_dangerous_good"]:
                ret.update(
                    {
                        f"HZ{count}": "Y",
                        f"HZUN{count}": package["un_number"],
                        f"HZCL{count}": package["class_div"],
                        f"HZPropName{count}": package["proper_shipping_name"],
                        f"HZPackGrp{count}": package["packing_group_str"],
                    }
                )

                if package["is_nos"] or package["is_neq"]:
                    ret[f"HZTechName{count}"] = package["dg_nos_description"]

            count += 1

        return ret

    def _build_request(self) -> dict:
        """
        Build ABF rate request Dictionary
        :return: ABF Rate Request Dictionary
        """
        test = "Y" if settings.DEBUG else "N"

        ret = {
            "ID": self._api_key,
            "Test": test,
            "QuoteID": self._service_parts[1],
            "RequesterType": "3",
            "PayTerms": "P",
            "ProAutoAssign": "Y",
            "Instructions": self._ubbe_request.get("special_instructions", "")[:250],
        }

        ret.update(self._build_requester_information())
        ret.update(self._build_address(key="Ship", address=self._origin, is_full=True))
        ret.update(
            self._build_address(key="Cons", address=self._destination, is_full=True)
        )
        ret.update(self._build_third_party())
        ret.update(self._build_packages())
        ret.update(self._build_reference_numbers())
        ret.update(
            self._build_options(options=self._ubbe_request.get("carrier_options", []))
        )
        ret.update(self._build_document_settings())

        if self._service_parts[0] in self._time_critical_service_codes:
            if "pickup" in self._ubbe_request:
                pickup_date = self._ubbe_request["pickup"]["date"]
            else:
                pickup_date = datetime.datetime.today().date()

            ret.update(
                {"TimeKeeper": "Y", "ShipDate": pickup_date.strftime("%m/%d/%Y")}
            )

        return ret

    def _determine_service_name(self, service_code: str) -> str:
        """
        Determine Serice Name from passd in code
        :param service_code: Code
        :return: Service Name
        """

        if service_code in self._time_critical_service_codes:
            return f"Guaranteed {service_code}"

        if service_code == "SV":
            return "Spot LTL"

        return service_code

    def _get_documents(self, urls: list) -> list:
        """
        Get Documents for shipment, should have BOL and shipping Labels.
        :param urls: list of Document Urls
        :return: list of document dicts
        """
        documents = []

        for url, doc_type in urls:
            try:
                document_bytes = self._get_content(url=url)
            except RequestError as e:
                connection.close()
                raise ShipException(f"ABF Ship (L373): {str(e)}") from e

            encoded = base64.b64encode(document_bytes)
            documents.append({"document": encoded.decode("ascii"), "type": doc_type})

        return documents

    def _format_response(self, response: dict) -> dict:
        """
        Format Response into ubbe response.
        :param response: ABF Response
        :return: ubbe response
        """
        surcharge_list = []

        if not response["ABF"]:
            raise ShipException("ABF Ship (L230): Error with Cached Rate.")

        response = response["ABF"]

        if int(response["NUMERRORS"]) > 0:
            message = str({"abf_ship": f"ABF Failure: {str(response['ERROR'])}"})
            CeleryLogger().l_critical.delay(
                location="abf_ship.py line: 227", message=message
            )
            raise ShipException("ABF Ship (L230): Request Error (Critical Email)")

        cached_rate = cache.get(self._ubbe_request["service_code"])

        if not cached_rate:
            raise ShipException("ABF Ship (L230): Error with Cached Rate.")

        service_name = self._determine_service_name(service_code=self._service_parts[0])

        documents = self._get_documents(
            urls=[
                (response["DOCUMENT"], DOCUMENT_TYPE_BILL_OF_LADING),
                (response["LABELDOCUMENT"], DOCUMENT_TYPE_SHIPPING_LABEL),
            ]
        )

        if self._service_parts[0] == "LTL":
            surcharge_list = cached_rate.get("surcharge_list", [])

        ret = {
            "carrier_id": ABF_FREIGHT,
            "carrier_name": self._carrier_name,
            "service_code": self._service_parts[0],
            "service_name": service_name,
            "freight": cached_rate["freight"],
            "surcharges": surcharge_list,
            "surcharges_cost": cached_rate["surcharge"],
            "tax_percent": cached_rate["tax_percent"],
            "taxes": cached_rate["tax"],
            "total": cached_rate["total"],
            "tracking_number": response["PRONUMBER"],
            "pickup_id": "",
            "transit_days": cached_rate["transit_days"],
            "delivery_date": cached_rate["delivery_date"],
            "carrier_api_id": self._service_parts[1],
            "documents": documents,
        }

        self._apply_exchange_rate(rate=ret, is_ship=True)

        return ret

    def ship(self) -> dict:
        """
        Ship ABF shipment.
        :return:
        """

        if self._origin["country"] not in ["CA", "US", "MX"] or self._destination[
            "country"
        ] not in ["CA", "US", "MX"]:
            connection.close()
            raise ShipException(
                "ABF Ship (L275): No service available (Country:CA,US,MX)."
            )

        if (
            self._origin["province"] in self._north
            or self._destination["province"] in self._north
        ):
            connection.close()
            raise ShipException(
                "ABF Ship (L275): No service available (North:YT,NT,NU)."
            )

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise ShipException(f"ABF Ship (L286): {str(e)}") from e

        try:
            response = self._get(url=self._ship_url, params=request)
        except RequestError as e:
            connection.close()
            raise ShipException(f"ABF Ship (L292): {str(e)}") from e

        if response.get("is_error", True):
            connection.close()
            raise ShipException(f"ABF Ship (L292): {str(response)}")

        try:
            response = self._format_response(response=response["response"])
        except ShipException as e:
            connection.close()
            raise ShipException(
                f"ABF Ship (L298): {str(e.message)}\n{response}\n{request}"
            ) from e
        except Exception as e:
            connection.close()
            raise ShipException(
                f"ABF Ship (L301): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return response
