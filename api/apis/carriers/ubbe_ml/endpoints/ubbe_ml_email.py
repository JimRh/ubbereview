"""
    Title: ubbe ML Email Carrier Api
    Description: TThis file will contain functions related to ubbe ML Email Api.
    Created: Feb 15, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy

from api.background_tasks.emails import CeleryEmail


class MLCarrierEmail:
    """
    ubbe ML Carrier Email class
    """

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)

        if "dg_service" in self._ubbe_request:
            del self._ubbe_request["dg_service"]

        if "objects" in self._ubbe_request:
            del self._ubbe_request["objects"]

        if "other_legs" in self._ubbe_request:
            del self._ubbe_request["other_legs"]

    def _clean_data(self) -> None:
        """
        Clean ubbe data for email.
        :return:
        """
        for request_package in self._ubbe_request["packages"]:
            if request_package["is_dangerous_good"]:
                del request_package["dg_object"]

    def manual_email(self, ship_data: dict) -> dict:
        """
        Send email request to book shipment to Customer Service.
        :param ship_data:
        :return:
        """
        self._clean_data()
        CeleryEmail().mlcarrier_email.delay(
            copy.deepcopy(self._ubbe_request), ship_data["documents"], ship_data
        )

        return {
            "pickup_id": "",
            "pickup_message": "Pickup has been requested",
            "pickup_status": "Success",
        }
