import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class UnitedStates(SOAPObj):
    def __init__(self, postal_code: str) -> None:
        self._postal_code = postal_code
        self._clean()

    # Override
    def _clean(self) -> None:
        if re.fullmatch(POSTAL_CODE_REGEX["US"], self._postal_code) is None:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.UnitedStates": "Zip code does not follow format 99999"
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {"zip-code": self._postal_code}
