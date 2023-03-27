from api.apis.carriers.fedex.soap_objects.common.version_id import VersionId
from api.apis.carriers.fedex.soap_objects.common.web_authentication_detail import (
    WebAuthenticationDetail,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.soap_objects.track.client_detail import ClientDetail
from api.apis.carriers.fedex.soap_objects.track.track_selection_detail import (
    TrackSelectionDetail,
)


# TODO add auth params


class TrackRequest(FedExSoapObject):
    _required_keys = {"WebAuthenticationDetail", "ClientDetail", "Version"}
    _optional_keys = {
        "TransactionDetail",
        "SelectionDetails",
        "TransactionTimeOutValueInMilliseconds",
        "ProcessingOptions",
    }

    def __init__(self, tracking_number: str, carrier_account):
        version = VersionId(
            {
                "ServiceId": "trck",
                "Major": 16,
                "Intermediate": 0,
                "Minor": 0,
            }
        )

        client = ClientDetail(
            account_number=carrier_account.account_number.decrypt(),
            meter_number=carrier_account.contract_number.decrypt(),
        )

        auth = WebAuthenticationDetail(
            key=carrier_account.api_key.decrypt(),
            password=carrier_account.password.decrypt(),
        )

        super().__init__(
            {
                "WebAuthenticationDetail": auth.data,
                "ClientDetail": client.data,
                "Version": version.data,
                "SelectionDetails": [
                    TrackSelectionDetail(tracking_number=tracking_number).data
                ],
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
