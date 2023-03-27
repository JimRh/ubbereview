from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class ExportDetail(FedExSoapObject):
    _optional_keys = {
        "B13AFilingOption",
        "ExportComplianceStatement",
        "PermitNumber",
        "DestinationControlDetail",
    }

    def __init__(self):
        super().__init__(
            {"B13AFilingOption": "MANUALLY_ATTACHED"},
            optional_keys=self._optional_keys,
        )
