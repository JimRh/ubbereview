from api.apis.carriers.fedex.globals.globals import (
    LABEL_IMAGE_TYPE,
    LABEL_STOCK_TYPE,
    LABEL_PRINTING_ORIENTATION,
    LABEL_ORDER,
    SHIPPING_LABEL_FORMAT_TYPE,
)
from api.apis.carriers.fedex.soap_objects.common.customer_specified_label_detail import (
    CustomerSpecifiedLabelDetail,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class LabelSpecification(FedExSoapObject):
    _required_keys = {
        "LabelFormatType",
    }
    _optional_keys = {
        "ImageType",
        "LabelStockType",
        "LabelPrintingOrientation",
        "LabelOrder",
        "PrintedLabelOrigin",
        "CustomerSpecifiedDetail",
    }

    def __init__(self):
        super().__init__(
            {
                "LabelFormatType": SHIPPING_LABEL_FORMAT_TYPE,
                "ImageType": LABEL_IMAGE_TYPE,
                "LabelStockType": LABEL_STOCK_TYPE,
                "LabelPrintingOrientation": LABEL_PRINTING_ORIENTATION,
                "LabelOrder": LABEL_ORDER,
                # 'PrintedLabelOrigin': None,
                "CustomerSpecifiedDetail": CustomerSpecifiedLabelDetail().data,
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
