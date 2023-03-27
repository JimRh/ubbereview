import copy
import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class AddressDetails(SOAPObj):
    def __init__(self, address: dict) -> None:
        self._address = address
        self._postal_code = copy.deepcopy(address["postal_code"])
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._address["address"]) > 44:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AddressDetails": "Destination key 'Address' greater than "
                    "44 characters"
                }
            )

        if len(self._address["city"]) > 40:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AddressDetails": "Destination key 'City' greater than 40 characters"
                }
            )

        if len(self._address["province"]) > 20:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AddressDetails": "Destination key 'Province' greater than "
                    "20 characters"
                }
            )

        if len(self._address["country"]) > 2:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.AddressDetails": "Destination key 'Country' greater than 2 characters"
                }
            )
        self._address["country"] = self._address["country"].upper()
        country_code = self._address["country"]

        if country_code in {"CA", "US"}:
            self._postal_code = self._postal_code.replace(" ", "").upper()

            if re.fullmatch(POSTAL_CODE_REGEX[country_code], self._postal_code) is None:
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.AddressDetails": "Destination key 'PostalCode' does not match "
                        + POSTAL_CODE_REGEX[country_code]
                    }
                )
        else:
            if len(self._address) > 14:
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.AddressDetails": "Destination key 'PostalCode' greater than "
                        "14 characters"
                    }
                )

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "address-line-1": self._address["address"],
            "city": self._address["city"],
            "prov-state": self._address["province"],
            "country-code": self._address["country"],
            "postal-zip-code": self._postal_code,
        }
