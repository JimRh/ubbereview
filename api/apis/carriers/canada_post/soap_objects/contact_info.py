import copy
import re
from typing import Union

import phonenumbers

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class ContactInfo(SOAPObj):
    def __init__(self, origin: dict) -> None:
        self._origin = copy.deepcopy(origin)
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._origin["name"]) > 45:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ContactInfo": "Origin key 'Name' greater than 45 characters"
                }
            )

        if len(self._origin["email"]) > 60:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ContactInfo": "Origin key 'Email' greater than 60 characters"
                }
            )

        if (
            re.fullmatch(
                r"(['\w\-+]+)(\.['\w\-+]+)*@([A-Z\d\-]+)(\.[A-Z\d\-]+)*(\.[A-Z]{2,5})",
                self._origin["email"],
                re.IGNORECASE,
            )
            is None
        ):
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ContactInfo": r"Origin email does not match "
                    r"'(['\w\-+]+)(\.['\w\-+]+)*@([A-Za-z\d\-]+)(\.[A-Za-z\d\-]+)*(\.[A-Za-z]{2,5})'"
                }
            )

        if len(self._origin["phone"]) > 16:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ContactInfo": "Origin key 'Phone' greater than 16 characters"
                }
            )

        try:
            raw_phone = phonenumbers.parse(
                self._origin["phone"], self._origin["country"].upper()
            )
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ContactInfo": "Phone number parser: "
                    + str(e)
                }
            )
        number_format = phonenumbers.NumberFormat(
            pattern="(\\d{3})(\\d{3})(\\d{4})", format="\\1-\\2-\\3"
        )
        self._origin["phone"] = phonenumbers.format_by_pattern(
            raw_phone, phonenumbers.PhoneNumberFormat.NATIONAL, [number_format]
        )

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "contact-name": self._origin["name"],
            "email": self._origin["email"],
            "contact-phone": self._origin["phone"],
        }
