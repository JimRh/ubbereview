from api.apis.carriers.fedex.globals.globals import EXPORT_TYPE, EXPORT_DESCRIPTION
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CustomsOptionDetail(FedExSoapObject):
    _optional_keys = {"Type", "Description"}

    def __init__(self):
        super().__init__(
            {"Type": EXPORT_TYPE, "Description": EXPORT_DESCRIPTION},
            optional_keys=self._optional_keys,
        )
