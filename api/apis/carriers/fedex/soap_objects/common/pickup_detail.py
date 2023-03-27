import datetime

from api.apis.carriers.fedex.globals.globals import (
    SAME_DAY_PICKUP_REQUEST,
    FUTURE_PICKUP_REQUEST,
    PICKUP_REQUEST_SOURCE,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.globals.project import (
    DEFAULT_PICKUP_START,
    DEFAULT_PICKUP_DATE,
    DEFAULT_PICKUP_END,
)


class PickupDetail(FedExSoapObject):
    _optional_keys = {
        "ReadyDateTime",
        "LatestPickupDateTime",
        "CourierInstructions",
        "RequestType",
        "RequestSource",
    }

    def __init__(self, pickup: dict):
        super().__init__(
            {"RequestSource": PICKUP_REQUEST_SOURCE}, optional_keys=self._optional_keys
        )
        pickup_date = pickup.get("date", DEFAULT_PICKUP_DATE())
        pickup_start = pickup.get("start_time", DEFAULT_PICKUP_START)
        pickup_end = pickup.get("end_time", DEFAULT_PICKUP_END)

        ready = datetime.datetime.strptime(
            "{} {}".format(pickup_date.strftime("%Y-%m-%d"), pickup_start),
            "%Y-%m-%d %H:%M",
        )
        end = datetime.datetime.strptime(
            "{} {}".format(pickup_date.strftime("%Y-%m-%d"), pickup_end),
            "%Y-%m-%d %H:%M",
        )

        self.add_values(ReadyDateTime=ready, LatestPickupDateTime=end)

        if pickup_date == datetime.datetime.today().date():
            request_type = SAME_DAY_PICKUP_REQUEST
        else:
            request_type = FUTURE_PICKUP_REQUEST

        self.add_value("RequestType", request_type)
