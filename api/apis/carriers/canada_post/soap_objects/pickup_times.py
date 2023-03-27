from typing import Union

from api.apis.carriers.canada_post.soap_objects.on_demand_pickup_time import (
    OnDemandPickupTime,
)
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class PickupTimes(SOAPObj):
    def __init__(self, pickup_datetime: dict) -> None:
        self._pickup_datetime = pickup_datetime

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "on-demand-pickup-time": OnDemandPickupTime(self._pickup_datetime).data(),
        }
