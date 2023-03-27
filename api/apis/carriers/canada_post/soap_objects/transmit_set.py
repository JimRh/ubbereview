import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.manifest_address import ManifestAddress
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class TransmitSet(SOAPObj):
    def __init__(self, order_number: str, origin_postal_code: str) -> None:
        self._order_number = order_number
        self._origin_postal_code = origin_postal_code
        self._clean()

    # Override
    def _clean(self) -> None:
        if re.fullmatch(POSTAL_CODE_REGEX["CA"], self._origin_postal_code) is None:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.TransmitSet": "Origin key 'PostalCode' does not match "
                    + POSTAL_CODE_REGEX["CA"]
                }
            )

        if len(self._order_number) > 32:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.TransmitSet": "Group id greater than 32 characters"
                }
            )

        if self._order_number:
            if re.fullmatch(r"([A-Z\d]+)", self._order_number, re.IGNORECASE) is None:
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.TransmitSet": r"Customer reference does not match '([A-Z\d]+)'"
                    }
                )

    # Override
    def data(self) -> Union[list, dict]:
        bbe_address = {
            "company_name": "BBE EXPEDITING LTD",
            "phone": "7808906893",
            "address": "1759 35 AVENUE EAST",
            "city": "EDMONTON INTERNATIONAL AIRPORT",
            "postal_code": "T9E0V6",
            "province": "AB",
            "country": "CA",
        }
        return {
            "group-ids": [self._order_number],
            "cpc-pickup-indicator": True,
            "requested-shipping-point": self._origin_postal_code.replace(" ", ""),
            "detailed-manifests": False,
            "method-of-payment": "Account",
            "manifest-address": ManifestAddress(bbe_address).data(),
            "customer-reference": self._order_number[:12],
        }
