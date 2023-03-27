from datetime import datetime
from typing import Any, Dict

from api.apis.carriers.fedex.soap_objects.common.contact_and_address import (
    ContactAndAddress,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class PickupOriginDetail(FedExSoapObject):
    _optional_keys = {
        "UseAccountAddress",
        "AddressId",  # FedEx internal use only
        "PickupLocation",
        "PackageLocation",
        "BuildingPart",
        "BuildingPartDescription",
        "ReadyTimestamp",
        "CompanyCloseTime",
        "StayLate",  # FedEx internal use only
        "PickupDateType",  # FedEx internal use only
        "LastAccessTime",  # FedEx internal use only
        "GeographicalPostalCode",  # European pickups only
        "Location",  # FedEx internal use only
        "DeleteLastUsed",  # FedEx internal use only
        "SuppliesRequested",
        "EarlyPickup",  # European pickups only
    }

    def __init__(self, gobox_request: Dict[str, Any]):
        pickup_data = gobox_request["pickup"]
        pickup_date = datetime.combine(pickup_data["date"], datetime.min.time())
        start_parts = pickup_data["start_time"].split(":")
        end_parts = pickup_data["end_time"].split(":")

        ready_time = pickup_date.replace(
            hour=int(start_parts[0]),
            minute=int(start_parts[1]),
            second=0,
            microsecond=0,
        )
        close_time = pickup_date.replace(
            hour=int(end_parts[0]), minute=int(end_parts[1]), second=0, microsecond=0
        )

        super().__init__(
            {
                "UseAccountAddress": False,
                "PickupLocation": ContactAndAddress(
                    party_details=gobox_request["origin"]
                ).data,
                "ReadyTimestamp": ready_time,
                "CompanyCloseTime": close_time.time(),
                "PackageLocation": "NONE",
            },
            optional_keys=self._optional_keys,
        )
