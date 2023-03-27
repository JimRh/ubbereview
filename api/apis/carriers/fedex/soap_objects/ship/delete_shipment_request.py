from api.apis.carriers.fedex.soap_objects.common.tracking_id import TrackingId
from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.ship.client_detail import ClientDetail
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class DeleteShipmentRequest(FedExSoapObject):
    _required_keys = {
        "WebAuthenticationDetail",
        "ClientDetail",
        "Version",
        "DeletionControl",
    }
    _optional_keys = {"TransactionDetail", "ShipTimestamp", "TrackingId"}

    def __init__(self, tracking_number: str):
        super().__init__(
            {
                "WebAuthenticationDetail": WebAuthenticationDetail().data,
                "ClientDetail": ClientDetail().data,
                "Version": VersionId(
                    version={
                        "ServiceId": "ship",
                        "Major": 23,
                        "Intermediate": 0,
                        "Minor": 0,
                    }
                ).data,
                "DeletionControl": "DELETE_ALL_PACKAGES",
                "TrackingId": TrackingId(tracking_number=tracking_number).data,
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
