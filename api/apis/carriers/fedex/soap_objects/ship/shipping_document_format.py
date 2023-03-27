from api.apis.carriers.fedex.globals.globals import LABEL_IMAGE_TYPE
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class ShippingDocumentFormat(FedExSoapObject):
    _optional_keys = {
        "Dispositions",
        "TopOfPageOffset",
        "ImageType",
        "StockType",
        "ProvideInstructions",
        "OptionsRequested",
        "Localization",
        "CustomDocumentIdentifier",
    }

    def __init__(self):
        super().__init__(
            {
                "ImageType": LABEL_IMAGE_TYPE,
                "StockType": "PAPER_LETTER",
                "ProvideInstructions": True,
            },
            optional_keys=self._optional_keys,
        )
