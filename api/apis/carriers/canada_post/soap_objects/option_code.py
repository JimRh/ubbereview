import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class OptionCode(SOAPObj):
    def __init__(self, option_code: str) -> None:
        self._option_code = option_code
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._option_code) > 10:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Option": "Option '{}' greater than 10 characters".format(
                        self._option_code
                    )
                }
            )

        if re.fullmatch(r"([A-Z\d]+)", self._option_code, re.IGNORECASE) is None:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Option": "Option code is not alphanumeric"
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {"option-code": self._option_code}
