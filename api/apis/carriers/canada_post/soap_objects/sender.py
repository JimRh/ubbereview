from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.address_details import AddressDetails
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class Sender(SOAPObj):
    _str_max_len = 44

    def __init__(self, origin: dict) -> None:
        self._origin = origin
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._origin["name"]) > self._str_max_len:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Sender": "Destination key 'Name' greater than "
                    + str(self._str_max_len)
                    + " characters"
                }
            )

        if len(self._origin["company_name"]) > self._str_max_len:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Sender": "Destination key 'CompanyName' greater than "
                    + str(self._str_max_len)
                    + " characters"
                }
            )

        if len(self._origin["phone"]) > 25:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Sender": "Destination key 'Phone' greater than 25 characters"
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "name": self._origin["name"],
            "company": self._origin["company_name"],
            "contact-phone": self._origin["phone"],
            "address-details": AddressDetails(self._origin).data(),
        }
