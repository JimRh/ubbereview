from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation import validators


class ClientDetail(FedExSoapObject):
    _required_keys = {"AccountNumber", "MeterNumber"}
    _optional_keys = {"IntegratorId", "Localization"}
    _validators = {"MeterNumber": validators.MeterNumber}

    def __init__(self, account_number, meter_number):
        super().__init__(
            {"AccountNumber": account_number, "MeterNumber": meter_number},
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
            validators=self._validators,
        )
