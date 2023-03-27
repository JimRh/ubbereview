"""
    Title: ABF Pickup api
    Description: This file will contain functions related to ABF Pickup Api.
    Created: June 27, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

from django.db import connection

from api.apis.carriers.abf_freight.endpoints.abf_base import ABFFreightBaseApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, PickupException
from brain import settings


class ABFPickup(ABFFreightBaseApi):
    """
    ABF Fright Pickup Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._service_parts = self._ubbe_request["service_code"].split("|")

    @staticmethod
    def _format_response(response: dict) -> dict:
        """
        Format ABF Pickup Response into ubbe Response
        :return: ubbe Pickup Response
        """
        ret = {"pickup_id": "", "pickup_message": "Success", "pickup_status": "Booked"}

        if "ABF" not in response:
            ret["pickup_message"] = "(ABF) Pickup Request Failed."
            ret["pickup_status"] = "Failed"
            return ret

        response = response["ABF"]

        if int(response["NUMERRORS"]) > 0:
            CeleryLogger().l_critical.delay(
                location="abf_ship.py line: 46",
                message=str({"abf_rate": f"ABF Failure: {str(response['ERROR'])}"}),
            )
            error = response["ERROR"]
            ret["pickup_message"] = f"{error['ERRORMESSAGE']}({error['ERRORCODE']})."
            ret["pickup_status"] = "Failed"
            return ret

        ret["pickup_id"] = response.get("CONFIRMATION", "")

        return ret

    def _build_packages(self) -> dict:
        """
        Build ABF Packages from ubbe packages.
        :return: dictionary of ABF Packages
        """
        ret = {}
        count = 1

        for package in self._ubbe_request["packages"]:
            ret.update(
                {
                    f"Desc{count}": package["description"],
                    f"PN{count}": package["quantity"],
                    f"PT{count}": self._package_type_map[package["package_type"]],
                    f"WT{count}": Decimal(
                        package["imperial_weight"] * package["quantity"]
                    ).quantize(self._sig_fig),
                    f"CL{count}": self._freight_class_map[package["freight_class"]],
                }
            )

            if package["is_dangerous_good"]:
                ret[f"HZ{count}"] = "Y"

            count += 1

        return ret

    def _build_pickup(self) -> dict:
        """
        Build ABF Pickup Details from ubbe pickup if exists, otherwise use today.
        :return: ABF Pickup Dictionary
        """

        if "pickup" in self._ubbe_request:
            pickup_date = self._ubbe_request["pickup"]["date"]
            start_time = self._ubbe_request["pickup"]["start_time"]
            end_time = self._ubbe_request["pickup"]["end_time"]
        else:
            pickup_date = datetime.datetime.today().date()
            start_time = "09:00"
            end_time = "18:00"

        return {
            "PickupDate": pickup_date.strftime("%m/%d/%Y"),
            "AT": start_time,
            "OT": start_time,
            "CT": end_time,
        }

    def _build_request(self) -> dict:
        """
        Build ABF Pickup Request.
        :return: dictionary of pickup request
        """
        test = "Y" if settings.DEBUG else "N"

        ret = {
            "ID": self._api_key,
            "Test": test,
            "RequesterType": "3",
            "PayTerms": "P",
            "Pronumber": self._ubbe_request["tracking_number"],
            "Instructions": self._ubbe_request.get("special_instructions", "")[:250],
        }

        if self._service_parts[0] in self._time_critical_service_codes:
            ret.update({"TimeKeeper": "Y"})

        ret.update(self._build_requester_information())
        ret.update(self._build_address(key="Ship", address=self._origin, is_full=True))
        ret.update(
            self._build_address(key="Cons", address=self._destination, is_full=True)
        )
        ret.update(self._build_third_party())
        ret.update(self._build_reference_numbers())
        ret.update(
            self._build_options(options=self._ubbe_request.get("carrier_options", []))
        )
        ret.update(self._build_pickup())

        return ret

    def pickup(self) -> dict:
        """
        Pickup YRC shipment.
        :return:
        """

        try:
            request = self._build_request()
        except KeyError as e:
            connection.close()
            raise PickupException(f"ABF Pickup (L157): {str(e)}") from e

        if not request:
            connection.close()
            raise PickupException("ABF Pickup (L161): Failed Building Request.")

        try:
            response = self._get(url=self._pickup_url, params=request)
        except RequestError as e:
            connection.close()
            raise PickupException(f"ABF Pickup (L167): {str(e)}") from e

        if response.get("is_error", True):
            connection.close()
            raise PickupException(f"ABF Pickup (L292): {str(response)}")

        try:
            response = self._format_response(response=response["response"])
        except Exception as e:
            connection.close()
            raise PickupException(
                f"ABF Pickup (L177): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return response
