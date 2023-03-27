from api.apis.carriers.fedex.globals.globals import (
    LABEL_FORMAT_TYPE,
    LABEL_IMAGE_TYPE,
    LABEL_STOCK_TYPE,
    LABEL_PRINTING_ORIENTATION,
    LABEL_ROTATION,
    LABEL_ORDER,
)
from api.apis.carriers.fedex.soap_objects.common.customer_specified_label_detail import (
    CustomerSpecifiedLabelDetail,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class LabelSpecification(FedExSoapObject):
    _optional_keys = {
        "LabelFormatType",
        "ImageType",
        "LabelStockType",
        "LabelPrintingOrientation",
        "LabelRotation",
        "LabelOrder",
        "PrintedLabelOrigin",
        "CustomerSpecifiedDetail",
    }

    def __init__(self):
        super().__init__(
            {
                "LabelFormatType": LABEL_FORMAT_TYPE,
                "ImageType": LABEL_IMAGE_TYPE,
                "LabelStockType": LABEL_STOCK_TYPE,
                "LabelPrintingOrientation": LABEL_PRINTING_ORIENTATION,
                "LabelRotation": LABEL_ROTATION,
                "LabelOrder": LABEL_ORDER,
                # 'PrintedLabelOrigin': None,
                "CustomerSpecifiedDetail": CustomerSpecifiedLabelDetail().data,
            },
            optional_keys=self._optional_keys,
        )
