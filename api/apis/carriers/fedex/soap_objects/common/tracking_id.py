from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation.validators import TrackingNumber


class TrackingId(FedExSoapObject):
    _optional_keys = {"TrackingIdType", "FormId", "UspsApplicationId", "TrackingNumber"}
    _validators = {"TrackingNumber": TrackingNumber}

    def __init__(self, tracking_number):
        super().__init__(
            {"TrackingNumber": tracking_number, "TrackingIdType": "FEDEX"},
            optional_keys=self._optional_keys,
            validators=self._validators,
        )
