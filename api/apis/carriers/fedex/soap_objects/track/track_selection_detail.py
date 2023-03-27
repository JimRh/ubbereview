from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.soap_objects.track.track_package_identifier import (
    TrackPackageIdentifier,
)


class TrackSelectionDetail(FedExSoapObject):
    _optional_keys = {
        "CarrierCode",
        "OperatingCompany",
        "PackageIdentifier",
        "TrackingNumberUniqueIdentifier",
        "ShipDateRangeBegin",
        "ShipDateRangeEnd",
        "ShipmentAccountNumber",
        "SecureSpodAccount",
        "Destination",
        "PagingDetail",
        "CustomerSpecifiedTimeOutValueInMilliseconds",
    }

    def __init__(self, tracking_number: str):
        super().__init__(
            {
                "PackageIdentifier": TrackPackageIdentifier(
                    tracking_number=tracking_number
                ).data
            },
            optional_keys=self._optional_keys,
        )
