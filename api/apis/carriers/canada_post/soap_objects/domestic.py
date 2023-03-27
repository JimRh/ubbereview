import copy
import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class Domestic(SOAPObj):
    def __init__(self, postal_code: str) -> None:
        self._postal_code = copy.deepcopy(postal_code)
        self._clean()

    # Override
    def _clean(self) -> None:
        self._postal_code = self._postal_code.replace(" ", "").upper()

        if re.fullmatch(POSTAL_CODE_REGEX["CA"], self._postal_code) is None:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Domestic": "Postal code does not follow format "
                    + POSTAL_CODE_REGEX["CA"]
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {"postal-code": self._postal_code}
