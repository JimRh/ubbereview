from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class TrackPackageIdentifier(FedExSoapObject):
    _required_keys = {"Type", "Value"}

    def __init__(self, tracking_number: str):
        super().__init__(
            {"Type": "TRACKING_NUMBER_OR_DOORTAG", "Value": tracking_number},
            required_keys=self._required_keys,
        )
