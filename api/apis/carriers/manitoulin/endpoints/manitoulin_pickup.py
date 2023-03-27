"""
    Title: Manitoulin Pickup api
    Description: This file will contain functions related to Manitoulin Pickup Api.
    Created: January 03, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""

import datetime
from decimal import Decimal, ROUND_UP

from django.db import connection

from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi
from api.exceptions.project import RequestError, PickupException
from api.globals.carriers import MANITOULIN
from api.models import CityNameAlias


class ManitoulinPickup(ManitoulinBaseApi):
    """
    Manitoulin Pickup Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

    @staticmethod
    def _build_address(address: dict, is_shipper: bool = False) -> dict:
        """
        Build Manitoulin Address layout for shipper and consignee.
        :param address: Origin or Destination address dictionary and is_shipper boolean
        :param is_shipper: boolean
        :return: Manitoulin Address dict
        """
        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=MANITOULIN,
        )

        ret = {
            "address": address["address"],
            "address_2": address.get("address", "address_two"),
            "city": city,
            "postal": address["postal_code"],
            "province": address["province"],
            "company": address["company_name"],
            "contact": address["name"],
            "phone": address["phone"],
            "email": address["email"],
        }

        if is_shipper:
            ret["private_residence"] = not address["has_shipping_bays"]

        return ret

    @staticmethod
    def _build_third_party() -> dict:
        """
        Build Manitoulin ship third party dictionary. Defaults to BBE.
        :return: Manitoulin third party dict
        """
        return {
            "company": "BBE Expediting LTD",
            "contact": "Customer Service",
            "phone": "8884206926",
        }

    @staticmethod
    def _format_response(response: dict) -> dict:
        """
        Format Manitoulin Pickup Response into ubbe Response
        :return: ubbe Pickup Response
        """
        pickup_id = ""
        ret = {
            "pickup_id": pickup_id,
            "pickup_message": "(Manitoulin) Pickup Failed.",
            "pickup_status": "Failed",
        }

        if response != {} and response["punum"]:
            ret["pickup_id"] = response["punum"]
            ret["pickup_message"] = "Success"
            ret["pickup_status"] = "Booked"

        return ret

    def _build_packages(self) -> tuple:
        """
        Build Manitoulin Packages from ubbe packages.
        :return: dictionary of Manitoulin Packages
        """

        description = ""
        package_list = []

        for package in self._ubbe_request["packages"]:
            description += f'{package["description"]}, '
            package_list.append(
                {
                    "item_class": self._freight_class_map[
                        package.get("freight_class", "70.00")
                    ],
                    "package_code": self._pickup_package_type_map[
                        package["package_type"]
                    ],
                    "pieces": package["quantity"],
                    "weight": int(
                        package["imperial_weight"].quantize(
                            Decimal("1"), rounding=ROUND_UP
                        )
                    ),
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
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                }
            )

        return package_list, description

    def _build_pickup(self) -> dict:
        """
        Build Manitoulin Pickup Details from ubbe pickup if exists, otherwise use today.
        :return: Manitoulin Pickup Dictionary
        """

        if "pickup" in self._ubbe_request:
            pickup_date = self._ubbe_request["pickup"]["date"]
            ready_time = self._ubbe_request["pickup"]["start_time"]
            closing_time = self._ubbe_request["pickup"]["end_time"]
        else:
            pickup_date = datetime.datetime.today().date()
            ready_time = "09:00"
            closing_time = "18:00"

        return {
            "pickup_date": pickup_date.strftime("%Y-%m-%d"),
            "ready_time": ready_time,
            "closing_time": closing_time,
        }

    def _build_request(self):
        """
        Build Manitoulin Pickup request Dictionary
        :return: Manitoulin Pickup Request Dictionary
        """
        service_parts = self._ubbe_request["service_code"].split("|")
        service_code = service_parts[0]

        items, description = self._build_packages()

        special_instructions = self._ubbe_request.get("special_instructions")

        if not special_instructions:
            special_instructions = self._ubbe_request.get("order_number", "ubbe")

        ret = {
            "requester": "Third Party",
            "shipper": self._build_address(
                address=self._ubbe_request["origin"], is_shipper=True
            ),
            "consignee": self._build_address(address=self._ubbe_request["destination"]),
            "items": items,
            "description": description[:20],
            "special_pickup_instruction": special_instructions[:27],
            "special_delivery_instruction": special_instructions[:27],
            "freight_charge_party": "Third Party Prepaid",
            "third_party": self._build_third_party(),
            "confirm_pickup_receipt": True,
            "recipient": {
                "company": "BBE Expediting Ltd",
                "contact": "Customer Service",
                "email": "customerservice@ubbe.com",
                "contact_by": "Email",
                "pickup_confirmation": True,
            },
        }

        ret.update(self._build_pickup())

        if service_code != "LTL":
            ret.update(
                {
                    "guaranteed_service": True,
                    "guaranteed_option": "By noon"
                    if service_code == "ROCKA"
                    else "By 4pm",
                }
            )

        return ret

    def pickup(self) -> dict:
        """
        Creates Manitoulin Pickup and returns resposne in ubbe format.
        :return: ubbe response
        """

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise PickupException(f"Manitoulin Pickup (L157): {str(e)}") from e

        if not request:
            connection.close()
            raise PickupException("Manitoulin Pickup (L161): Failed Building Request.")

        try:
            response = self._post(url=self._pickup_url, request=request)
        except RequestError as e:
            connection.close()
            raise PickupException(f"Manitoulin Pickup (L167): {str(e)}") from e

        if not response.get("punum"):
            connection.close()
            raise PickupException(f"Manitoulin Pickup (L292): {str(response)}")

        try:
            response = self._format_response(response=response)
        except Exception as e:
            connection.close()
            raise PickupException(
                f"Manitoulin Pickup (L177): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return response
