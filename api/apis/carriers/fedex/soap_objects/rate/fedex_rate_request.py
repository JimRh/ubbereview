from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.rate.client_detail import ClientDetail
from api.apis.carriers.fedex.soap_objects.rate.requested_shipment import (
    RequestedShipment,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class FedExRateRequest(FedExSoapObject):
    _required_keys = {
        "WebAuthenticationDetail",
        "ClientDetail",
        "Version",
    }
    _optional_keys = {
        "TransactionDetail",
        "ReturnTransitAndCommit",
        "CarrierCodes",
        "VariableOptions",
        "ConsolidationKey",
        "RequestedShipment",
    }

    def __init__(self, gobox_request: dict):
        version = VersionId(
            version={"ServiceId": "crs", "Major": 24, "Intermediate": 0, "Minor": 0}
        )

        client = ClientDetail(
            account_number=gobox_request["account_number"],
            meter_number=gobox_request["meter_number"],
        )

        auth = WebAuthenticationDetail(
            key=gobox_request["key"],
            password=gobox_request["password"],
        )

        super().__init__(
            {
                "WebAuthenticationDetail": auth.data,
                "ClientDetail": client.data,
                "Version": version.data,
                "ReturnTransitAndCommit": True,
                "RequestedShipment": RequestedShipment(
                    gobox_request=gobox_request
                ).data,
            },
            self._required_keys,
            self._optional_keys,
        )
