from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation import validators


class Address(FedExSoapObject):
    _optional_keys = {
        "StreetLines",
        "City",
        "StateOrProvinceCode",
        "PostalCode",
        "UrbanizationCode",
        "CountryCode",
        "CountryName",
        "Residential",
        "GeographicCoordinates",
    }
    _validators = {
        "StreetLines": validators.AddressLine,
        "City": validators.City,
        "StateOrProvinceCode": validators.State,
        "PostalCode": validators.Postal,
    }

    def __init__(self, address_details: dict):
        super().__init__(
            {
                "StreetLines": [
                    s
                    for s in [
                        address_details.get("address", ""),
                        address_details.get("address_two", ""),
                    ]
                    if s
                ],
                "City": address_details.get("city", ""),
                "PostalCode": address_details.get("postal_code", ""),
                "CountryCode": address_details.get("country", ""),
                "Residential": not address_details.get("has_shipping_bays", True),
            },
            optional_keys=self._optional_keys,
            validators=self._validators,
        )

        if address_details.get("country", "") in ["CA", "US"]:
            self.add_value("StateOrProvinceCode", address_details["province"])
