from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation import validators


class Address(FedExSoapObject):
    _required_keys = {
        "PostalCode",
        "CountryCode",
    }

    _validators = {
        "StateOrProvinceCode": validators.State,
        "PostalCode": validators.Postal,
    }

    def __init__(self, address_details: dict):
        super().__init__(
            {
                "PostalCode": address_details.get("postal_code", ""),
                "CountryCode": address_details.get("country", ""),
            },
            required_keys=self._required_keys,
            validators=self._validators,
        )
