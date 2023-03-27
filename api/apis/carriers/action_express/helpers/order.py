"""
    Title: Action Express Order
    Description: This file will contain helper functions related to ction Express Order specs.
    Created: June 14, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal, ROUND_UP

from dateutil.tz import tz

from api.globals.carriers import ACTION_EXPRESS
from api.models import CityNameAlias


class Order:
    """
    Action Express Order Object Class
    """

    _linear_weight = 10

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = ubbe_request

    @staticmethod
    def _create_item(package: dict) -> dict:
        """
        Create Package Item
        :return: dict of ontime360 Item
        """

        return {
            "Description": package.get("description", "Box"),
            "Length": package["imperial_length"],
            "Width": package["imperial_width"],
            "Height": package["imperial_height"],
            "Weight": package["imperial_weight"],
        }

    def _create_address(self, key: str) -> dict:
        """
        Create address information for request based on the address key.
        :return: ontime360 Address dict
        """

        city = CityNameAlias.check_alias(
            alias=self._ubbe_request[key]["city"],
            province_code=self._ubbe_request[key]["province"],
            country_code=self._ubbe_request[key]["country"],
            carrier_id=ACTION_EXPRESS,
        )

        try:
            postal_code = f'{self._ubbe_request[key]["postal_code"][0:3]} {self._ubbe_request[key]["postal_code"][3:6]}'
        except Exception:
            postal_code = self._ubbe_request[key]["postal_code"]

        return {
            "ContactName": self._ubbe_request[key].get("name", ""),
            "CompanyName": self._ubbe_request[key]["company_name"],
            "AddressLine1": self._ubbe_request[key]["address"],
            "AddressLine2": self._ubbe_request[key].get("address_two", ""),
            "City": city,
            "State": self._ubbe_request[key]["province"],
            "PostalCode": postal_code,
            "Country": self._ubbe_request[key]["country"],
            "Email": "customerservice@ubbe.com",
            "Phone": self._ubbe_request[key].get("phone", ""),
        }

    def _create_pickup(self) -> dict:
        """
        Create pickup information for request
        :return: ontime360 pickup dict
        """

        if "pickup" not in self._ubbe_request:
            return {}

        pickup = self._ubbe_request["pickup"]
        from_zone = tz.gettz("America/Edmonton")
        to_zone = tz.gettz("UTC")

        start_time = datetime.datetime.strptime(
            f'{pickup["date"]} {pickup["start_time"]}', "%Y-%m-%d %H:%M"
        )
        end_time = datetime.datetime.strptime(
            f'{pickup["date"]} {pickup["end_time"]}', "%Y-%m-%d %H:%M"
        )

        start_time = start_time.replace(tzinfo=from_zone)
        end_time = end_time.replace(tzinfo=from_zone)

        start_time = start_time.astimezone(to_zone)
        end_time = end_time.astimezone(to_zone)

        return {
            "EarliestTime": start_time.isoformat(),
            "LatestTime": end_time.isoformat(),
        }

    def _create_items(self, description: str) -> tuple:
        """
        Create list of Package Items.
        :return: list of ontime360 Item
        """
        packages = []

        for package in self._ubbe_request["packages"]:
            new_package = self._create_item(package=package)
            dims = f'{new_package["Length"]}x{new_package["Width"]}x{new_package["Height"]}'
            description += f'\n{new_package["Description"]}\n{package["quantity"]} - {dims} @ {new_package["Weight"]}'
            packages.append(new_package)

        return description, packages

    def create_order(self, customer: str, price_set: str) -> dict:
        """
        Create list of Package Items.
        :return: list of ontime360 Item
        """
        shipment_id = self._ubbe_request.get("order_number", "")

        if "awb" in self._ubbe_request:
            ref = f'{self._ubbe_request["awb"]}/{self._ubbe_request.get("reference_one", "")}'
        else:
            ref = f'{self._ubbe_request.get("reference_one", "")}/{self._ubbe_request.get("reference_two", "")}'[
                :50
            ]

        description = f'{shipment_id}\n{ref}: {self._ubbe_request.get("special_instructions", "")}'
        description, packages = self._create_items(description=description)

        dimensional_weight = (
            self._ubbe_request["total_volume_imperial"] * self._linear_weight
        )
        final_weight = max(
            dimensional_weight, self._ubbe_request["total_weight_imperial"]
        )

        ret = {
            "Customer": customer,
            "PriceSet": price_set,
            "CustomerContact": {
                "CustomerID": customer,
                "Name": "Customer Service",
                "Email": "customerservice@ubbe.ca",
                "Phone": "8884206926",
            },
            "Items": packages,
            "CollectionLocation": self._create_address(key="origin"),
            "DeliveryLocation": self._create_address(key="destination"),
            "CollectionArrivalWindow": self._create_pickup(),
            "RequestedBy": "ubbe (BBE Expediting Ltd)",
            "Description": description,
            "CollectionSignatureRequired": True,
            "DeliverySignatureRequired": True,
            # "DeclaredValue": 100.0,
            "ReferenceNumber": ref,
            "PurchaseOrderNumber": shipment_id,
            "Comments": self._ubbe_request.get("special_instructions", ""),
            "Weight": Decimal(final_weight).quantize(Decimal("1"), rounding=ROUND_UP),
            "Quantity": self._ubbe_request["total_quantity"],
            "PriceModifiers": [],
        }

        return ret
