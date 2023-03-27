"""
    Title: YRC Pickup api
    Description: This file will contain functions related to YRC Ship Api.
    Created: January 20, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import math

from django.db import connection

from api.apis.carriers.yrc.endpoints.yrc_base import YRCBaseApi
from api.exceptions.project import RequestError, PickupException
from api.globals.carriers import YRC
from api.models import CityNameAlias


class YRCPickup(YRCBaseApi):
    """
    YRC Fright Pickup Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self.request = {}
        self._response = {}

    @staticmethod
    def _build_third_party() -> dict:
        """
        Build YRC ship third party dictionary. Defaults to BBE.
        :return: YRC third party section
        """

        return {
            "role": "Third Party",
            "company": "BBE Expediting LTD",
            "address": "1759-35 Ave E",
            "city": "Edmonton Intl Airport",
            "state": "AB",
            "postalCode": "T9E0V6",
            "country": "CAN",
            "contact": {
                "name": "Customer Service",
                "email": "customerservice@ubbe.com",
                "phone": "888-420-6926",
            },
        }

    def _format_response(self, response: dict) -> None:
        """
        Format YRC pickup response into ubbe format.
        :param response: YRC Pickup Response
        :return: Pickup details
        """
        pickup_id = ""

        if "masterId" in response:
            pickup_id = response["masterId"]
        else:
            for reference_id in response["referenceIds"]:
                pickup_id = reference_id

        self._response = {
            "pickup_id": pickup_id,
            "pickup_message": "Booked",
            "pickup_status": "Success",
            "is_direct": response["isDirect"],
            "is_weather": response["isWeatherAlert"],
        }

    def _build_destination(self) -> dict:
        """
        Build yrc pickup request login section and remove unneeded fields.
        :return:
        """

        destination = self._build_location(address=self._ubbe_request["destination"])
        del destination["contact"]

        return destination

    def _build_location(self, address: dict) -> dict:
        """
        Build YRC ship third party dictionary. Defaults to BBE.
        :return: YRC third party section
        """

        country = address["country"]

        if country == self._US:
            country = self._USA
        elif country == self._MX:
            country = self._MEX
        else:
            country = self._CAN

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=YRC,
        )

        return {
            "company": address["company_name"],
            "address": address["address"],
            "city": city,
            "state": address["province"],
            "postalCode": address["postal_code"],
            "country": country,
            "contact": {
                "name": address["name"],
                "email": address["email"],
                "phone": address["phone"],
            },
        }

    def _build_login(self) -> dict:
        """
        Build yrc pickup request login section and remove unneeded fields.
        :return:
        """

        auth = self._build_json_auth()
        del auth["busId"]
        del auth["busRole"]
        del auth["paymentTerms"]

        return auth

    def _build_shipments(self, destination: dict) -> list:
        """
        Build Shipment items
        :param destination: Destination for shipment in yrc format.
        :return:
        """
        package_list = []
        service_parts = self._ubbe_request["service_code"].split("|")
        service_code = service_parts[0]

        for package in self._ubbe_request["packages"]:
            package_code = "PLT"

            if package["package_type"] in self.pickup_package_type_map:
                package_code = self.pickup_package_type_map[package["package_type"]]

            ret = {
                "destination": destination,
                "pieces": package["quantity"],
                "pieceType": package_code,
                "weightLbs": math.ceil(int(package["imperial_weight"])),
                "length": math.ceil(int(package["imperial_length"])),
                "width": math.ceil(int(package["imperial_width"])),
                "height": math.ceil(int(package["imperial_height"])),
                "service": self._rate_to_pickup_services[service_code],
                "paymentTerms": "PPD",
                "isFood": False,
                "isPoison": False,
                "isCertified": False,
                "isHazardous": package["is_dangerous_good"],
                "isFreezable": False,
                "isEmailConfirmation": False,
                "trackingType": "PO",
                "trackingNumber": self._ubbe_request["order_number"],
            }

            if package["is_dangerous_good"]:
                ret.update(
                    {
                        "placardType": "UN",
                        "placardNumber": package["class_div"],
                    }
                )

            package_list.append(ret)

        return package_list

    def _create_request(self) -> dict:
        """
        Build YRC pickup request.
        :return: pickup request
        """

        pickup = self._ubbe_request["pickup"]
        destination = self._build_destination()
        special = self._remove_special_characters(
            string_value=self._ubbe_request.get("special_instructions", "")[:75]
        )

        ret = {
            "login": self._build_login(),
            "requester": self._build_third_party(),
            "pickupLocation": self._build_location(
                address=self._ubbe_request["origin"]
            ),
            "pickupDate": pickup["date"].strftime("%m/%d/%Y"),
            "readyTime": pickup["start_time"],
            "closeTime": pickup["end_time"],
            "isLiftgate": False,
            "pickupNotes": special,
            "shipments": self._build_shipments(destination=destination),
        }

        return ret

    def pickup(self) -> dict:
        """
        Pickup YRC shipment.
        :return:
        """

        try:
            request = self._create_request()
        except KeyError as e:
            connection.close()
            raise PickupException(f"YRC Pickup (L221): {str(e)}") from e

        try:
            response = self._post(url=self._pickup_url, request=request)
        except RequestError as e:
            connection.close()
            raise PickupException(f"YRC Pickup (L227): {str(e)}") from e

        if not response["isSuccess"]:
            connection.close()
            raise PickupException(
                f'YRC Pickup (L231): Pickup Failed {str(response["errors"])}.'
            )

        try:
            self._format_response(response=response)
        except Exception as e:
            connection.close()
            raise PickupException(
                f"YRC Pickup (L237): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return self._response
