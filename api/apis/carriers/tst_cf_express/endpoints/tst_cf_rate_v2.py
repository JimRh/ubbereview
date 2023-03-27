"""
    Title: TST CF Express Rate api
    Description: This file will contain functions related to TST CF Express rate Api.
    Created: January 10, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import math
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_base_v2 import TstCfExpressApi
from api.exceptions.project import RateException, RequestError
from api.globals.carriers import TST
from api.models import CityNameAlias
from brain.settings import CACHE_TTL


class TstCfExpressRate(TstCfExpressApi):
    """
    TST CF Express Rate Class

    Units: Imperial Units are used for this api
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._origin = self._ubbe_request.get("origin", {})
        self._destination = self._ubbe_request.get("destination", {})

        self._requests = []
        self._responses = []

    @staticmethod
    def _format_surcharges(response, total) -> dict:
        """
        Format surcharges for to ubbe rate response
        :return: Dict containing surcharges and tax
        """
        total_tax = Decimal("0")
        surcharges = Decimal("0")
        total_tax_percent = Decimal("0.00")
        surcharge_list = []
        tax_list = []

        for charge in response["accitems"]["item"]:
            cost = charge["itemamount"]

            if charge["itemcode"] in ["HST", "GST", "PST", "QST", "RST"]:
                tax = Decimal(str(cost))
                total_tax += tax
                tax_list.append(
                    {
                        "name": charge["itemcode"] + " - " + charge["itemdesc"],
                        "cost": tax,
                        "percentage": Decimal("0.00"),
                    }
                )
            else:
                surcharge_list.append(
                    {
                        "name": charge["itemcode"] + " - " + charge["itemdesc"],
                        "cost": Decimal(str(cost)),
                        "percentage": Decimal("0.00"),
                    }
                )

                surcharges += Decimal(str(cost))

        sub_total = total - total_tax

        for tax in tax_list:
            tax_percent = round(
                tax["cost"] / Decimal(str(sub_total)) * Decimal("100"), 0
            )
            total_tax_percent += tax_percent

            tax["percentage"] = Decimal(str(tax_percent))
            surcharge_list.append(tax)

        return {
            "tax": total_tax,
            "tax_list": tax_list,
            "surcharges": surcharges,
            "surcharge_list": surcharge_list,
            "total_tax_percent": total_tax_percent,
        }

    def _build_address(self, key: str, address: dict) -> etree.Element:
        """
        Create address lxml object for request
        :param key: address dict key: "origin" or "destination"
        :param address: address dictionary
        :return: address lxml object
        """

        request_address = etree.Element(key)

        city = CityNameAlias.check_alias(
            address["city"], address["province"], address["country"], TST
        )

        request_address.append(
            self._add_child(element="zip", value=address["postal_code"])
        )
        request_address.append(self._add_child(element="city", value=city))
        request_address.append(
            self._add_child(element="state", value=address["province"])
        )

        return request_address

    def _build_packages(self, package_list: list) -> etree.Element:
        """
        Create lxml package data for request
        :return: package lxml object
        """
        packages = etree.Element("shipdetail")

        for package in package_list:
            quantity = package["quantity"]
            weight = package["imperial_weight"]

            line = etree.Element("line")
            line.append(
                self._add_child(
                    element="weight", value=str(math.ceil(weight * quantity))
                )
            )

            if package.get("freight_class"):
                line.append(
                    self._add_child(
                        element="class",
                        value=self._freight_classes[package["freight_class"]],
                    )
                )

            dimensions = etree.Element("dimensions")
            dimensions.append(self._add_child(element="qty", value=str(quantity)))
            dimensions.append(
                self._add_child(
                    element="len", value=str(math.ceil(package["imperial_length"]))
                )
            )
            dimensions.append(
                self._add_child(
                    element="wid", value=str(math.ceil(package["imperial_width"]))
                )
            )
            dimensions.append(
                self._add_child(
                    element="hgt", value=str(math.ceil(package["imperial_height"]))
                )
            )
            line.append(dimensions)
            packages.append(line)

        return packages

    def _build(self, service_code: str) -> etree.Element:
        """
        Build base request for tst-cf rate
        :return:
        """
        base = etree.Element("raterequest")

        self._add_auth(request=base)

        # Only add for testing.
        if self._is_test:
            base.append(self._add_child(element="testmode", value="Y"))

        base.append(self._add_child(element="service", value=service_code))
        base.append(self._add_child(element="funds", value="C"))
        base.append(self._add_child(element="rqby", value="3"))
        base.append(self._add_child(element="terms", value="P"))
        base.append(self._add_child(element="taxexempt", value="N"))
        base.append(self._add_child(element="language", value="en"))
        base.append(self._add_child(element="transit", value="Y"))

        base.append(self._build_address(key="origin", address=self._origin))
        base.append(self._build_address(key="destination", address=self._destination))
        base.append(self._build_packages(package_list=self._ubbe_request["packages"]))

        if "carrier_options" in self._ubbe_request:
            base.append(self._build_options())

        return base

    def _format_response(self, response: dict) -> None:
        """
        Format response for to ubbe rate response
        :param response: response from carrier api
        :return: None
        """

        service_code = f'{self._road_service}-{response["quoteid"]}'

        total = Decimal(str(response["totalamt"])).quantize(Decimal(".01"))
        charge_data = self._format_surcharges(response=response, total=total)
        freight = Decimal(str(response["freightamt"])).quantize(Decimal(".01"))
        discount = Decimal(str(response["discountamt"])).quantize(Decimal(".01"))
        freight -= discount

        transit_days, delivery_date = self._format_values(data=response)

        ret = {
            "carrier_id": TST,
            "carrier_name": self._carrier_name,
            "service_code": service_code,
            "service_name": self._services_names[self._road_service],
            "freight": freight,
            "surcharge": charge_data["surcharges"],
            "surcharge_list": charge_data["surcharge_list"],
            "tax": charge_data["tax"],
            "tax_percent": charge_data["total_tax_percent"].quantize(Decimal("1")),
            "total": total,
            "transit_days": transit_days,
            "delivery_date": delivery_date,
        }

        cache.set(service_code, {"tst": response, "ubbe": ret}, CACHE_TTL)

        g1_service = Decimal(str(response["g1amt"])).quantize(Decimal(".01"))
        g2_service = Decimal(str(response["g2amt"])).quantize(Decimal(".01"))
        g3_service = Decimal(str(response["g3amt"])).quantize(Decimal(".01"))

        if g1_service is not None:
            self._format_services(
                service_code=self._g1_service,
                service_price=g1_service,
                response=response,
                ubbe_response=copy.deepcopy(ret),
            )

        if g2_service is not None:
            self._format_services(
                service_code=self._g2_service,
                service_price=g2_service,
                response=response,
                ubbe_response=copy.deepcopy(ret),
            )

        if g3_service is not None:
            self._format_services(
                service_code=self._g3_service,
                service_price=g3_service,
                response=response,
                ubbe_response=copy.deepcopy(ret),
            )

        del ret["surcharge_list"]
        self._responses.append(ret)

    def _format_services(
        self,
        service_code: str,
        service_price: Decimal,
        response: dict,
        ubbe_response: dict,
    ) -> None:
        """

        :param response:
        :param ubbe_response:
        :return:
        """

        pre_tax = service_price / (1 + (ubbe_response["tax_percent"] / 100))
        tax = service_price - pre_tax
        service_charge = pre_tax - ubbe_response["surcharge"] - ubbe_response["freight"]

        ubbe_response["service_code"] = f'{service_code}-{response["quoteid"]}'
        ubbe_response["service_name"] = self._services_names[service_code]
        ubbe_response["surcharge"] = Decimal(
            ubbe_response["surcharge"] + service_charge
        ).quantize(Decimal(".01"))
        ubbe_response["tax"] = Decimal(tax).quantize(Decimal(".01"))
        ubbe_response["total"] = Decimal(service_price).quantize(Decimal(".01"))

        ubbe_response["surcharge_list"].append(
            {
                "name": ubbe_response["service_name"],
                "cost": service_charge.quantize(Decimal(".01")),
                "percentage": Decimal("0.00"),
            }
        )

        cache_data = {
            "tst": response,
            "ubbe": ubbe_response,
            "service_info": {
                "service_charge": service_charge.quantize(Decimal(".01")),
                "surcharge": ubbe_response["surcharge"],
                "tax": ubbe_response["tax"],
                "total": ubbe_response["total"],
            },
        }

        cache.set(ubbe_response["service_code"], cache_data, CACHE_TTL)
        del ubbe_response["surcharge_list"]
        self._responses.append(ubbe_response)

    def rate(self) -> list:
        """
        Get rates for TST Overland
        :return: list of dictionary rates
        """

        if (
            self._origin["province"] in self._north
            or self._destination["province"] in self._north
        ):
            connection.close()
            raise RateException("TST-CF Rate (L187): Not Supported Region.")

        # build requests for TST
        try:
            request = self._build(service_code=self._road_service)
        except RateException as e:
            connection.close()
            raise RateException("TST-CF Rate (L187): Issue building Request.") from e

        # build requests
        try:
            response = self._post(
                url=self._rate_url, return_key="rqresults", request=request
            )
        except RequestError as e:
            connection.close()
            raise RateException(f"TST-CF Rate (L187): Failed Post. {str(e)}") from e

        # build requests
        try:
            self._format_response(response=response)
        except RequestError as e:
            connection.close()
            raise RateException(
                f"TST-CF Rate (L187): Failed Formatting. {str(e)}"
            ) from e

        connection.close()
        return self._responses

    # REVIEW THIS

    def get_rate_cost(self, service: str):

        request = self._build(service_code=service)

        response = self._post(url=self._rate_url, return_key="rqresults", request=request)

        formatted_response = self.format_response_ship(data=response, service_code=service)

        return formatted_response

    def format_response_ship(self, data, service_code):
        """
        Format response for to ubbe rate response
        @param data: data from carrier api
        @param service_code:
        :return: formatted rate dictionary
        """
        service_code = f'{service_code}-{data["quoteid"]}'
        total = Decimal(str(data["totalamt"])).quantize(Decimal(".01"))
        charge_data = self._format_surcharges(response=data, total=total)
        freight = Decimal(str(data["freightamt"])).quantize(Decimal(".01"))
        discount = Decimal(str(data["discountamt"])).quantize(Decimal(".01"))
        freight -= discount

        transit_days, delivery_date = self._format_values(data=data)

        return {
            'carrier_id': TST,
            'carrier_name': self._carrier_name,
            'service_code': service_code,
            'service_name': self._services_names[service_code],
            "surcharges_list": charge_data["surcharges_list"],
            'freight': freight,
            'surcharge': charge_data["surcharges"],
            'tax': charge_data["tax"],
            'tax_percent': charge_data["total_tax_percent"],
            'total': total,
            'transit_days': transit_days,
            'delivery_date': delivery_date
        }
