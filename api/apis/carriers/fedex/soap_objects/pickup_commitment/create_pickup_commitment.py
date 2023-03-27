from datetime import datetime

from api.apis.carriers.fedex.globals.globals import SERVICES_CA_DICT, SERVICES_INT_DICT
from api.apis.carriers.fedex.soap_objects.pickup_commitment.address import Address
from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.pickup_commitment.client_detail import (
    ClientDetail,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CreatePickupCommitmentRequest(FedExSoapObject):
    _required_keys = {
        "WebAuthenticationDetail",
        "ClientDetail",
        "TransactionDetail",
        "Version",
        "Origin",
        "Destination",
        "ShipDate",
        "CarrierCode",
    }
    _optional_keys = {"Service", "Packaging"}

    def __init__(self, pickup_request: dict):
        version = VersionId(
            version={
                "ServiceId": "vacs",
                "Major": 8,
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

        if pickup_request["service_code"] == "92":
            carrier_code = "FDXG"
        else:
            carrier_code = "FDXE"

        if pickup_request["is_international"]:
            service_type = SERVICES_INT_DICT[pickup_request["service_code"]]
        else:
            service_type = SERVICES_CA_DICT[pickup_request["service_code"]]

        super().__init__(
            {
                "WebAuthenticationDetail": auth.data,
                "ClientDetail": client.data,
                "Version": version.data,
                "Origin": Address(address_details=pickup_request["origin"]).data,
                "Destination": Address(
                    address_details=pickup_request["destination"]
                ).data,
                "ShipDate": pickup_request["pickup"]["date"].strftime("%Y-%m-%d"),
                "CarrierCode": carrier_code,
                "Service": service_type,
                "TransactionDetail": {
                    "CustomerTransactionId": "ServiceAvailabilityRequest"
                },
                "Packaging": "YOUR_PACKAGING",
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
