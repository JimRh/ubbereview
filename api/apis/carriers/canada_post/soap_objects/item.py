from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Item(SOAPObj):
    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "customs-number-of-units": "",
            "customs-description": "",
            "sku": "",
            "hs-tariff-code": "",
            "unit-weight": "",
            "customs-value-per-unit": "",
            "customs-unit-of-measure": "",
            "country-of-origin": "",
            "province-of-origin": "",
        }
