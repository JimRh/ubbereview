from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation.validators import Name


class CommercialInvoice(FedExSoapObject):
    _optional_keys = {
        "Comments",
        "FreightCharge",
        "TaxesOrMiscellaneousCharge",
        "TaxesOrMiscellaneousChargeType",
        "PackingCosts",
        "HandlingCosts",
        "SpecialInstructions",
        "DeclarationStatement",
        "PaymentTerms",
        "Purpose",
        "OriginatorName",
        "TermsOfSale",
    }
    _validators = {
        "OriginatorName": Name,
    }

    def __init__(self):
        super().__init__(
            {
                # 'Comments': None,
                # 'FreightCharge': None,
                # 'TaxesOrMiscellaneousCharge': None,
                # 'TaxesOrMiscellaneousChargeType': None,
                # 'PackingCosts': None,
                # 'HandlingCosts': None,
                # 'SpecialInstructions': None,
                # 'DeclarationStatement': None,
                # 'PaymentTerms': None,
                "Purpose": "SOLD",
                # 'OriginatorName': None,
                # 'TermsOfSale': TERMS_OF_SALE
            },
            optional_keys=self._optional_keys,
            validators=self._validators,
        )
