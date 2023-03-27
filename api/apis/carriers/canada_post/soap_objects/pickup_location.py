from typing import Union

from api.apis.carriers.canada_post.soap_objects.alternate_address import (
    AlternateAddress,
)
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class PickupLocation(SOAPObj):
    def __init__(self, origin: dict) -> None:
        self._origin = origin

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "business-address-flag": False,
            "alternate-address": AlternateAddress(self._origin).data(),
        }
