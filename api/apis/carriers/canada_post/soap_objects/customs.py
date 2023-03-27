from typing import Union

from api.apis.carriers.canada_post.soap_objects.items import Items
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


# Pending future technology & data
class Customs(SOAPObj):
    def __init__(self) -> None:
        pass

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "currency": "",
            "conversion-from-cad": "",
            "reason-for-export": "",
            "other-reason": "",  # Optional
            "sku-list": Items().data(),
            "certificate-number": "",
            "license-number": "",
            "invoice-number": "",
        }
