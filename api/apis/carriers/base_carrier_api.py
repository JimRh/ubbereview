"""
    Title: Base Carrier Api
    Description: This file will contain abstract functions that must be implemented when intergrating a carrier api.
    Created: Jan 6, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from abc import ABC, abstractmethod

from django.db import connection

from api.background_tasks.emails import CeleryEmail
from api.cache_lookups.api_cache import APICache
from api.exceptions.project import ViewException


class BaseCarrierApi(ABC):
    """
    Base Carrier Abstract Class
    """

    _carrier_api_name = ""
    _carrier_ids = []

    _default_pickup_error = {
        "pickup_id": "",
        "pickup_message": "Failed",
        "pickup_status": "Failed",
    }

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = ubbe_request
        # Configure Carrier Api
        # self._carrier = self.__get_carrier()
        # self._carrier_account = self.__get_carrier_account()

    def _check_active(self) -> None:
        """
        Check if the api is currently active for the system. Raise ViewException if not active.
        """
        if not self._carrier_api_name:
            connection.close()
            raise ViewException(f"class variable '_carrier_api_name' must be set.")

        api = APICache().get_api_cache(api_name=self._carrier_api_name)

        if not api.get("is_active", False):
            connection.close()
            raise ViewException(f"{self._carrier_api_name} (L46): Api not active.")

    # def __get_carrier(self) -> Carrier:
    #     """
    #     Get Carrier Object for carrier api.
    #     :return: Carrier Object
    #     """
    #     look_up = f"carrier_object_{self._carrier_id}"
    #     carrier = cache.get(look_up)
    #
    #     if not carrier:
    #
    #         try:
    #             carrier = Carrier.objects.get(code=self._carrier_id)
    #         except ObjectDoesNotExist:
    #             raise ViewException("Carrier Not Found.")
    #
    #         cache.set(look_up, carrier, TWENTY_FOUR_HOURS_CACHE_TTL)
    #
    #     return carrier

    # def __get_carrier_account(self) -> CarrierAccount:
    #     """
    #     Get Carrier Object for carrier api.
    #     :return:
    #     """
    #     look_up = f"carrier_account_object_{str(self._sub_account.subaccount_number)}_{self._carrier.code}"
    #     carrier_account = cache.get(look_up)
    #
    #     if not carrier_account:
    #
    #         try:
    #             carrier_account = CarrierAccount.objects.get(subaccount=self._sub_account, carrier=self._carrier)
    #         except ObjectDoesNotExist:
    #             carrier_account = CarrierAccount.objects.get(subaccount__is_default=True, carrier=self._carrier)
    #
    #         cache.set(look_up, carrier_account, TWENTY_FOUR_HOURS_CACHE_TTL)
    #
    #     return carrier_account

    @abstractmethod
    def rate(self) -> list:
        """
        Get Rates from carrier api endpoint and format into ubbe response.
        :return: list of dictionary rates
        """

    @abstractmethod
    def ship(self, order_number: str = "") -> dict:
        """
        Create Shipment from carrier api endpoint and format into ubbe response.
        :return: dictionary of shipment details.
        """

    @abstractmethod
    def pickup(self) -> dict:
        """
        Create Pickup for shipment from carrier api endpoint.
        :return: dictionary of pickup details.
        """

    @abstractmethod
    def track(self) -> dict:
        """
        Get Tracking information for shipment from carrier api endpoint.
        :return: dictionary of pickup details.
        """

    def document(self) -> dict:
        """
        Optional Override, get requested documents for shipment from carrier api endpoint.
        :return: list of dictionaries of document details.
        """

    def cancel(self) -> dict:
        """
        Cancel Shipment from carrier api endpoint. If endpoint does not exist, the base implementation will send
        an email to customer service to request cancel.

        Default Functionality: Send Email to Customer Service
        Override to implement carrier endpoint

        :return: Dictionary of cancel details.
        """

        CeleryEmail.cancel_shipment_email(request=self._ubbe_request)

        return {
            "is_canceled": False,
            "is_canceled_requested": True,
            "message": "Shipment Cancellation as been requested"
        }

    def cancel_pickup(self) -> dict:
        """
        Cancel Pickup from carrier api endpoint. If endpoint does not exist, the base implementation will send
        an email to customer service to request cancel of pickup

        Default Functionality: Send Email to Customer Service
        Override to implement carrier endpoint

        :return: Dictionary of cancel details.
        """

        CeleryEmail.cancel_pickup_email(request=self._ubbe_request)

        return {
            "is_canceled": False,
            "is_canceled_requested": True,
            "message": "Pickup Cancellation as been requested"
        }
