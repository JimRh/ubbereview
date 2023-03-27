from datetime import datetime

from api.apis.carriers.fedex.soap_objects.common.address import Address
from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.pickup.client_detail import ClientDetail
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class PickupAvailabilityRequest(FedExSoapObject):
    _required_keys = {"WebAuthenticationDetail", "ClientDetail", "Version"}
    _optional_keys = {
        "TransactionDetail",
        "PickupType",
        "AccountNumber",
        "PickupAddress",
        "PickupRequestType",
        "DispatchDate",
        "NumberOfBusinessDays",
        "PackageReadyTime",
        "CustomerCloseTime",
        "Carriers",
        "ShipmentAttributes",
        "PackageDetails",
    }

    def __init__(self, pickup_request: dict):
        version = VersionId(
            version={
                "ServiceId": "disp",
                "Major": 17,
                "Intermediate": 0,
                "Minor": 0,
            }
        )

        client = ClientDetail(
            account_number=pickup_request["account_number"],
            meter_number=pickup_request["meter_number"],
        )

        auth = WebAuthenticationDetail(
            key=pickup_request["key"],
            password=pickup_request["password"],
        )

        super().__init__(
            {
                "WebAuthenticationDetail": auth.data,
                "ClientDetail": client.data,
                "Version": version.data,
                "PickupAddress": Address(address_details=pickup_request["origin"]).data,
                "PickupRequestType": ["SAME_DAY"],
                "DispatchDate": datetime.strptime(
                    pickup_request["pickup"]["date"], "%Y-%m-%d"
                ),
                "PackageReadyTime": datetime.strptime(
                    pickup_request["pickup"]["start_time"], "%H:%M"
                ).time(),
                "CustomerCloseTime": datetime.strptime(
                    pickup_request["pickup"]["end_time"], "%H:%M"
                ).time(),
                "Carriers": ["FDXG", "FDXE"],
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
