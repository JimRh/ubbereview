from decimal import Decimal

from api.apis.carriers.fedex.globals.globals import KILOGRAMS
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation import validators


class Weight(FedExSoapObject):
    _optional_keys = {"Units", "Value"}
    _validators = {"Value": validators.Weight}

    def __init__(self, weight_value: Decimal):
        super().__init__(
            {"Units": KILOGRAMS, "Value": weight_value},
            optional_keys=self._optional_keys,
            validators=self._validators,
        )
