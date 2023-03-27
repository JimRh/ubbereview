from decimal import Decimal
from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class ItemsCharacteristics(SOAPObj):
    def __init__(self, world_request: dict) -> None:
        self._world_request = world_request

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        priority_service_qualifier = "PC"
        data = {"heavy-item-flag": False, "priority-flag": False}

        if any(
            Decimal(package["weight"]) >= 23
            for package in self._world_request["packages"]
        ):
            data["heavy-item-flag"] = True

        if priority_service_qualifier in self._world_request["service_code"]:
            data["priority-flag"] = True
        return data
