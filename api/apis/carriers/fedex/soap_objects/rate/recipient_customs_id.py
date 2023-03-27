from api.apis.carriers.fedex.globals.globals import EXPORT_RECIPIENT_TYPE
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class RecipientCustomsId(FedExSoapObject):
    _optional_keys = {"Type", "Value"}

    def __init__(self, recipient: str):
        super().__init__(
            {"Type": EXPORT_RECIPIENT_TYPE, "Value": recipient},
            optional_keys=self._optional_keys,
        )
