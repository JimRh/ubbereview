import math

from api.apis.carriers.fedex.globals.globals import CENTIMETERS
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation.validators import Dimension


class Dimensions(FedExSoapObject):
    _optional_keys = {"Length", "Width", "Height", "Units"}
    _validators = {
        "Length": Dimension,
        "Width": Dimension,
        "Height": Dimension,
    }

    def __init__(self, package: dict):
        length = package["length"]
        width = package["width"]
        height = package["height"]
        super().__init__(
            {
                "Length": int(math.ceil(length)),
                "Width": int(math.ceil(width)),
                "Height": int(math.ceil(height)),
                "Units": CENTIMETERS,
            },
            optional_keys=self._optional_keys,
            validators=self._validators,
        )
