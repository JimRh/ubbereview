from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class PrintPreferences(SOAPObj):
    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "output-format": "4x6",
            "encoding": "PDF",
        }
