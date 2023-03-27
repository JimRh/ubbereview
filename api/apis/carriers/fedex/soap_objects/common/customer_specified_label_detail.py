from api.apis.carriers.fedex.soap_objects.common.localization import Localization
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class CustomerSpecifiedLabelDetail(FedExSoapObject):
    _optional_keys = {
        "DocTabContent",
        "CustomContentPosition",
        "CustomContent",
        "ConfigurableReferenceEntries",
        "MaskedData",
        "SecondaryBarcode",
        "TermsAndConditionsLocalization",
        "RegulatoryLabels",
        "AdditionalLabels",
        "AirWaybillSuppressionCount",
    }

    def __init__(self):
        super().__init__(
            {
                # 'MaskedData': None,
                "TermsAndConditionsLocalization": Localization().data,
                # 'RegulatoryLabels': None,
                # 'AdditionalLabels': None,
                # 'AirWaybillSuppressionCount': None,
            },
            optional_keys=self._optional_keys,
        )
