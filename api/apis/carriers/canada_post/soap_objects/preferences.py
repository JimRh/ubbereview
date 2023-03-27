from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Preferences(SOAPObj):
    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "show-packing-instructions": True,
            "show-postage-rate": False,
            "show-insured-value": False,
        }
