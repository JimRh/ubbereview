from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CustomerReference(FedExSoapObject):
    _required_keys = {"CustomerReferenceType", "Value"}

    def __init__(self, reference: str):
        super().__init__(
            {"CustomerReferenceType": "CUSTOMER_REFERENCE", "Value": reference[:20]},
            required_keys=self._required_keys,
        )
