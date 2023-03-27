from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.ship.client_detail import ClientDetail
from api.apis.carriers.fedex.soap_objects.ship.requested_shipment import (
    RequestedShipment,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class ProcessShipmentRequest(FedExSoapObject):
    _required_keys = {
        "WebAuthenticationDetail",
        "ClientDetail",
        "RequestedShipment",
        "Version",
    }
    _optional_keys = {"TransactionDetail"}

    def __init__(
        self,
        gobox_request: dict,
        master_tracking=None,
        sequence=None,
        num_packages: int = None,
    ):
        request = RequestedShipment(
            gobox_request=gobox_request,
            master_tracking=master_tracking,
            sequence=sequence,
            num_packages=num_packages,
        )

        version = VersionId(
            version={"ServiceId": "ship", "Major": 23, "Intermediate": 0, "Minor": 0}
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
                "RequestedShipment": request.data,
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
