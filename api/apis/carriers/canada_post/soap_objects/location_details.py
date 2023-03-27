from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class LocationDetails(SOAPObj):
    def __init__(self, special_instr: str) -> None:
        self._special_instr = special_instr
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._special_instr) > 132:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.LocationDetails": "Key 'SpecialInstructions' greater than "
                    "132 characters"
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {"pickup-instructions": self._special_instr}
