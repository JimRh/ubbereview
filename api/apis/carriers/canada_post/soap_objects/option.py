from typing import Union

from api.apis.carriers.canada_post.soap_objects.option_code import OptionCode
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Option(SOAPObj):
    def __init__(self, option_code: str) -> None:
        self._option_code = option_code

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {"option": OptionCode(self._option_code).data()}
