from api.apis.carriers.fedex.globals.globals import COMMERCIAL_INVOICE_TYPE
from api.apis.carriers.fedex.soap_objects.ship.commercial_invoice_detail import (
    CommercialInvoiceDetail,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class ShippingDocumentSpecification(FedExSoapObject):
    _optional_keys = {
        "ShippingDocumentTypes",
        "CertificateOfOrigin",
        "CommercialInvoiceDetail",
        "CustomPackageDocumentDetail",
        "ExportDeclarationDetail",
        "GeneralAgencyAgreementDetail",
        "NaftaCertificateOfOriginDetail",
        "Op900Detail",
        "DangerousGoodsShippersDeclarationDetail",
        "FreightAddressLabelDetail",
        "ReturnInstructionsDetail",
    }

    def __init__(self, is_international: bool = False):
        super().__init__(optional_keys=self._optional_keys)
        if is_international:
            self.add_values(
                {
                    "ShippingDocumentTypes": COMMERCIAL_INVOICE_TYPE,
                    "CommercialInvoiceDetail": CommercialInvoiceDetail().data,
                }
            )
