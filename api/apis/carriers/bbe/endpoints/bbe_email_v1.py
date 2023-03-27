"""
    Title: BBE Email Api
    Description: This file will contain functions related to BBE email Api.
    Created: July 13, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
from datetime import date

from django.core.exceptions import ObjectDoesNotExist

from api.background_tasks.emails import CeleryEmail
from api.globals.carriers import BBE
from api.models import CarrierAccount


class BBEEmail:
    """
    Class will handle all details about the shipment request email.
    """

    def __init__(self, ubbe_request: dict, response: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._response = copy.deepcopy(response)
        self._order_number = self._ubbe_request["order_number"]
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._service_code = self._ubbe_request["service_code"]
        self._sub_account = self._ubbe_request["objects"]["sub_account"]

        if "dg_service" in self._ubbe_request:
            del self._ubbe_request["dg_service"]

        if "objects" in self._ubbe_request:
            del self._ubbe_request["objects"]

    def _get_carrier_account(self):
        """
        Attempt to get carrier account for sub account. If does not exist, get the default account.
        :return: Carrier Account Object
        """

        try:
            # Get account for sub account
            carrier_account = self._sub_account.carrieraccount_subaccount.get(
                carrier=BBE
            )
        except ObjectDoesNotExist:
            # Get default account
            carrier_account = CarrierAccount.objects.get(
                carrier__code=BBE, subaccount__is_default=True
            )

        return carrier_account

    def _create_email_data(self):
        """
        Configure email data.
        :return: dicionary object.
        """
        today = date.today().strftime("%Y/%m/%d")
        carrier_account = self._get_carrier_account()

        self._ubbe_request["is_sealift"] = False
        self._ubbe_request["carrier_account"] = carrier_account.account_number.decrypt()
        self._ubbe_request["carrier_name"] = self._response["service_name"]
        self._ubbe_request["service_name"] = self._response["service_name"]

        if not self._ubbe_request.get("pickup"):
            self._ubbe_request["pickup"] = {
                "date": today,
                "start_time": "08:00",
                "end_time": "16:00",
            }

        for request_package in self._ubbe_request["packages"]:
            if request_package["is_dangerous_good"]:
                del request_package["dg_object"]

    def send_email(self):
        """
        Send the email.
        :return: None
        """
        self._create_email_data()
        CeleryEmail().bbe_email.delay(
            copy.deepcopy(self._ubbe_request), self._response["documents"]
        )

        return {
            "pickup_id": "",
            "pickup_message": "Pickup has been requested",
            "pickup_status": "Success",
        }
