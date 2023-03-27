from typing import Dict

from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class VersionId(FedExSoapObject):
    _required_keys = {
        "ServiceId",
        "Major",
        "Intermediate",
        "Minor",
    }

    def __init__(self, version: Dict):
        super().__init__(version, required_keys=self._required_keys)
