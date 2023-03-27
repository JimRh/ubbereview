import copy
import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class AlternateAddress(SOAPObj):
    def __init__(self, origin: dict) -> None:
        self._origin = origin
        self._postal_code = copy.deepcopy(origin["postal_code"])
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._origin["company_name"]) > 35:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AlternateAddress": "Origin key 'CompanyName' "
                    "greater than 35 characters"
                }
            )

        if len(self._origin["address"]) > 35:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AlternateAddress": "Origin key 'Address' greater than 35 characters"
                }
            )

        if len(self._origin["city"]) > 35:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AlternateAddress": "Origin key 'City' greater than 35 characters"
                }
            )

        if len(self._origin["province"]) > 2:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AlternateAddress": "Origin key 'Province' greater than 2 characters"
                }
            )

        self._postal_code = self._postal_code.replace(" ", "").upper()

        if re.fullmatch(POSTAL_CODE_REGEX["CA"], self._postal_code) is None:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AlternateAddress": "Origin key 'PostalCode' does not match "
                    + POSTAL_CODE_REGEX["CA"]
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "company": self._origin["company_name"],
            "address-line-1": self._origin["address"],
            "city": self._origin["city"],
            "province": self._origin["province"],
            "postal-code": self._postal_code,
        }
