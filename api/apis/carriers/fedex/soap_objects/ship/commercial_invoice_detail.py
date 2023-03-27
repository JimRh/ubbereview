from api.apis.carriers.fedex.soap_objects.ship.shipping_document_format import (
    ShippingDocumentFormat,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CommercialInvoiceDetail(FedExSoapObject):
    _optional_keys = {"Format", "CustomerImageUsages"}

    def __init__(self):
        super().__init__(
            {"Format": ShippingDocumentFormat().data},
            optional_keys=self._optional_keys,
        )
