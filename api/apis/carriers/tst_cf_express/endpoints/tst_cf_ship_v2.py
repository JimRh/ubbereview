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
from datetime import datetime, timedelta, date

from django.core.cache import cache
from django.db import connection
from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_base_v2 import TstCfExpressApi
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_rate_v2 import TstCfExpressRate
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import RateException, RequestError, ShipException
from api.globals.carriers import TST
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
)
from api.models import CityNameAlias


class TstCfExpressShip(TstCfExpressApi):
    """
    TST CF Express Ship Class

    Units: Imperial Units are used for this api
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._lookup = copy.deepcopy(self._ubbe_request["service_code"])
        service_code, quote_id = self._ubbe_request["service_code"].split("-")
        self._service_code = service_code
        self._quote_id = quote_id

        self._origin = self._ubbe_request.get("origin", {})
        self._destination = self._ubbe_request.get("destination", {})

        self._request = []
        self._response = {}

    def _build_address(self, elm_type: str, address: dict) -> etree.Element:
        """
        Create address lxml object for request
        :param address: address dictionary
        :return: address lxml object
        """
        province = address["province"]
        country = address["country"]

        city = CityNameAlias.check_alias(
            alias=address["city"],
            province_code=province,
            country_code=country,
            carrier_id=TST,
        )

        if country == "CA":
            country = "CN"

        request_address = etree.Element(elm_type)
        request_address.append(
            self._add_child(element="company", value=address["company_name"])
        )
        request_address.append(
            self._add_child(element="contact", value=address["name"])
        )
        request_address.append(self._add_child(element="phone", value=address["phone"]))
        request_address.append(
            self._add_child(element="address1", value=address["address"])
        )
        request_address.append(self._add_child(element="city", value=city))
        request_address.append(self._add_child(element="country", value=country))
        request_address.append(self._add_child(element="state", value=province))
        request_address.append(
            self._add_child(element="zip", value=address["postal_code"])
        )

        if "address_two" in address:
            request_address.append(
                self._add_child(element="address2", value=address["address_two"])
            )

        if "extension" in address:
            request_address.append(
                self._add_child(element="phoneext", value=address["extension"])
            )

        return request_address

    def _build_bill(self) -> etree.Element:
        """
        Create bill address lxml object for request
        :return: address lxml object
        """

        request_address = etree.Element("billto")
        request_address.append(
            self._add_child(element="company", value="BBE Expediting Ltd.")
        )
        request_address.append(
            self._add_child(element="address1", value="1759 - 35 Avenue East")
        )
        request_address.append(
            self._add_child(element="city", value="Edmonton International Airport")
        )
        request_address.append(self._add_child(element="state", value="AB"))
        request_address.append(self._add_child(element="zip", value="T9E0V6"))

        return request_address

    def _build_instructions(self, instructions: str) -> etree.Element:
        """
        Add any special instructions for the carrier into the request
        :return: option lxml object
        """

        special_instructions = etree.Element("si")
        special_instructions.append(
            self._add_child(element="description", value=instructions)
        )

        if "awb" in self._ubbe_request:
            air = self._ubbe_request["air_carrier"]
            awb = self._ubbe_request["awb"]

            statement = f"Please reference {air} Airway Bill: {awb} on arrival."

            special_instructions.append(
                self._add_child(element="description", value=statement)
            )

        return special_instructions

    def _build_packages(self, package_list: list) -> tuple:
        """
        Create lxml package data for request
        :return: package lxml object
        """
        packages = etree.Element("shipdetail")
        dimensions = etree.Element("dimensions")

        for package in package_list:
            try:
                pack_code = self._package_codes[package["package_type"]]
            except KeyError:
                pack_code = "PCS"

            quantity = package["quantity"]
            length = package["imperial_length"]
            width = package["imperial_width"]
            height = package["imperial_height"]
            weight = package["imperial_weight"] * quantity

            line = etree.Element("line")
            line.append(
                self._add_child(element="description1", value=package["description"])
            )
            line.append(self._add_child(element="pkg", value=pack_code))
            line.append(self._add_child(element="pcs", value=str(quantity)))
            line.append(self._add_child(element="swgt", value=str(math.ceil(weight))))

            if package.get("freight_class"):
                line.append(
                    self._add_child(
                        element="cls",
                        value=self._freight_classes[package["freight_class"]],
                    )
                )

            packages.append(line)

            dimensions.append(self._add_child(element="qty", value=str(quantity)))
            dimensions.append(
                self._add_child(element="len", value=str(math.ceil(length)))
            )
            dimensions.append(
                self._add_child(element="wid", value=str(math.ceil(width)))
            )
            dimensions.append(
                self._add_child(element="hgt", value=str(math.ceil(height)))
            )

        return packages, dimensions

    def _build_pickup(self, pickup: dict) -> tuple:
        """
        Process Pickup Times and validate times for tst values.
        :param pickup:
        :return:
        """

        if self._ubbe_request.get("do_not_pickup", False):
            date_object = datetime.now() + timedelta(days=30)
            pickup_date = date_object.strftime("%Y%m%d")
            ready = "1000"
            close = "1600"
        else:
            pickup_date = pickup["date"].strftime("%Y%m%d")
            ready = pickup["start_time"].replace(":", "")
            close = pickup["end_time"].replace(":", "")

        if int(ready) < 800:
            ready = "0800"
        elif int(ready) > 1700:
            date_object = pickup["date"] + timedelta(days=1)
            pickup_date = date_object.strftime("%Y%m%d")
            ready = "0800"
            close = "1600"

        if int(close) < 1200:
            close = "1200"

        return pickup_date, ready, close

    def _build_rqby(self, address: dict) -> etree.Element:
        """
        Create rqby lxml object for request - Main point of contact?
        :return: rqby lxml object
        """

        rqby = etree.Element("rqby")

        rqby.append(self._add_child(element="email", value=address["email"]))
        rqby.append(self._add_child(element="phone", value=address["phone"]))
        rqby.append(self._add_child(element="name", value=address["name"]))

        return rqby

    def _build(self) -> None:
        """
        Build request  lxml object for pickup request.
        :return: None
        """
        self._request = etree.Element("bolpickuprequest")

        # Add Auth to request
        self._add_auth(request=self._request)

        # Only add for testing.
        if self._is_test:
            self._request.append(self._add_child(element="testmode", value="Y"))

        self._request.append(self._add_child(element="language", value="en"))
        self._request.append(self._add_child(element="ptype", value="B"))
        self._request.append(self._add_child(element="kg", value="N"))

        # Assign Pro Number -> Always yes
        self._request.append(self._add_child(element="assignpro", value="Y"))
        self._request.append(self._add_child(element="rqnbr", value=self._quote_id))
        self._request.append(
            self._add_child(element="service", value=self._service_code)
        )

        # References
        self._request.append(
            self._add_child(element="bolnbr", value=self._ubbe_request["order_number"])
        )
        self._request.append(
            self._add_child(
                element="custrefnbr", value=self._ubbe_request["order_number"]
            )
        )
        self._request.append(
            self._add_child(
                element="ponbr", value=self._ubbe_request.get("reference_one", "")
            )
        )

        # Create Addresses Elements
        self._request.append(
            self._build_address(elm_type="shipper", address=self._origin)
        )
        self._request.append(
            self._build_address(elm_type="consignee", address=self._destination)
        )
        self._request.append(self._build_bill())
        self._request.append(self._build_rqby(address=self._origin))

        # Broker Name
        if self._ubbe_request.get("is_international", False):
            broker_name = self._ubbe_request.get("broker", {}).get("company_name", "")
            self._request.append(
                self._add_child(element="brokername", value=broker_name)
            )

        # Create Pickup Elements
        pickup_date, ready, close = self._build_pickup(
            pickup=self._ubbe_request.get("pickup", {})
        )
        self._request.append(self._add_child(element="pickupdate", value=pickup_date))
        self._request.append(self._add_child(element="readytime", value=ready))
        self._request.append(self._add_child(element="closetime", value=close))

        # Create Packages Elements
        packages, dimensions = self._build_packages(
            package_list=self._ubbe_request["packages"]
        )
        self._request.append(packages)
        self._request.append(dimensions)

        # Create Optional elements
        if "special_instructions" in self._ubbe_request:
            self._request.append(
                self._build_instructions(
                    instructions=self._ubbe_request["special_instructions"]
                )
            )

        if "carrier_options" in self._ubbe_request:
            self._request.append(self._build_options())

    def _format_pickup(self, response: dict) -> None:
        """

        :return:
        """

        pickup_id = ""
        pickup_message = "Failed"
        pickup_status = "Failed"
        pickup = response.get("pickup", {})

        if pickup:
            status = pickup.get("status", "CS")

            if status == "OK":
                pickup_message = "Booked"
                pickup_status = "Success"

            pickup_id = pickup.get("confnbr", "")

        self._response.update(
            {
                "pickup_id": pickup_id,
                "pickup_message": pickup_message,
                "pickup_status": pickup_status,
            }
        )

    def _format_rate(self) -> None:
        """

        :return:
        """

        # Attempt to get cache rate quote
        cached_rate_data = cache.get(self._lookup)

        if not cached_rate_data:
            # TODO - Think about this
            tst_rate = TstCfExpressRate(ubbe_request=self._ubbe_request)
            return tst_rate.get_rate_cost(service=self._service_code)

        ubbe_response = cached_rate_data["ubbe"]

        self._response.update(
            {
                "freight": ubbe_response["freight"],
                "surcharges": ubbe_response["surcharge_list"],
                "taxes": ubbe_response["tax"],
                "tax_percent": ubbe_response["tax_percent"],
                "total": ubbe_response["total"],
                "surcharges_cost": ubbe_response["surcharge"],
                "transit_days": ubbe_response["transit_days"],
                "delivery_date": ubbe_response["delivery_date"],
            }
        )

    def _format_documents(self, tst_base_64: str, pro: str) -> list:
        """
        Generate Documents for request
        :return: Return list of dictionary documents
        """
        self._ubbe_request["carrier"] = self._carrier_name
        self._ubbe_request["service_name"] = self._services_names[self._service_code]
        self._ubbe_request["bol"] = pro
        self._ubbe_request["bol_number"] = pro
        self._ubbe_request["order_date"] = date.today().strftime("%Y/%m/%d")
        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)

        piece_label = manual_docs.generate_cargo_label()

        if not tst_base_64:
            bol = manual_docs.generate_bol()
        else:
            bol = str(tst_base_64)

        return [
            {"document": piece_label, "type": DOCUMENT_TYPE_SHIPPING_LABEL},
            {"document": bol, "type": DOCUMENT_TYPE_BILL_OF_LADING},
        ]

    def _format_response(self, response: dict) -> None:
        """

        :param response:
        :return:
        """
        pro_number = str(response.get("pro", ""))

        try:
            bol_base_64 = response["bol"]["imagedata"]
        except Exception:
            bol_base_64 = ""

        documents = self._format_documents(tst_base_64=bol_base_64, pro=pro_number)

        self._response.update(
            {
                "carrier_id": self._carrier_id,
                "carrier_name": self._carrier_name,
                "service_code": self._service_code,
                "service_name": self._services_names[self._service_code],
                "tracking_number": pro_number,
                "carrier_api_id": self._quote_id,
                "documents": documents,
            }
        )

        self._format_pickup(response=response)
        self._format_rate()

    def ship(self) -> dict:
        """
        Get rates for TST Overland
        :return: list of dictionary rates
        """

        if (
            self._origin["province"] in self._north
            or self._destination["province"] in self._north
        ):
            connection.close()
            raise ShipException("TST-CF Ship (L187): Not Supported Region.")

        try:
            self._build()
        except RateException as e:
            connection.close()
            raise ShipException(
                f"2Ship Rate (L198): Failed building request. {e.message}"
            ) from e

        try:
            response = self._post(
                url=self._ship_url, return_key="bolpuresults", request=self._request
            )
        except RequestError as e:
            connection.close()
            raise ShipException(f"TST-CF Rate (L187): Failed Post. {str(e)}") from e

        try:
            self._format_response(response=response)
        except KeyError as e:
            connection.close()
            raise ShipException(f"2Ship Ship (L367): {str(e)}") from e

        return self._response
