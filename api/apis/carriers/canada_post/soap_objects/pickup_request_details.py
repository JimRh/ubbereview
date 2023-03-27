from typing import Union

from api.apis.carriers.canada_post.soap_objects.items_characteristics import (
    ItemsCharacteristics,
)
from api.apis.carriers.canada_post.soap_objects.contact_info import ContactInfo
from api.apis.carriers.canada_post.soap_objects.location_details import LocationDetails
from api.apis.carriers.canada_post.soap_objects.payment_info import PaymentInfo
from api.apis.carriers.canada_post.soap_objects.pickup_location import PickupLocation
from api.apis.carriers.canada_post.soap_objects.pickup_times import PickupTimes
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class PickupRequestDetails(SOAPObj):
    def __init__(self, world_request: dict) -> None:
        self._world_request = world_request
        self._total_pc, self._unique_pc = self._calc_pickup_volume()

    def _calc_pickup_volume(self) -> tuple:
        total = 0
        unique = 0

        for package in self._world_request["packages"]:
            total += package["quantity"]
            unique += 1

        return total, unique

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "pickup-type": "OnDemand",
            "pickup-location": PickupLocation(self._world_request["origin"]).data(),
            "contact-info": ContactInfo(self._world_request["origin"]).data(),
            "location-details": LocationDetails(
                self._world_request.get(
                    "special_instructions", "No special instructions supplied"
                )
            ).data(),
            "items-characteristics": ItemsCharacteristics(self._world_request).data(),
            "pickup-volume": "{} unique pkgs. Total: {} units".format(
                self._unique_pc, self._total_pc
            ),
            "pickup-times": PickupTimes(self._world_request["pickup"]).data(),
            "payment-info": PaymentInfo(self._world_request).data(),
        }
