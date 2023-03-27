from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.address_details import AddressDetails
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class ShipDestination(SOAPObj):
    _str_max_len = 44

    def __init__(self, destination: dict, is_international: bool = False) -> None:
        self._destination = destination
        self._is_international = is_international
        self._clean()

    # Override
    def _clean(self) -> None:
        if self._is_international:
            if len(self._destination["phone"]) > 25:
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.ShipDestination": "International Destination key 'Phone' greater "
                        "than 25 characters"
                    }
                )

        if len(self._destination["name"]) > self._str_max_len:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ShipDestination": "Destination key 'Name' greater than {} characters".format(
                        self._str_max_len
                    )
                }
            )

        if len(self._destination["company_name"]) > self._str_max_len:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ShipDestination": "Destination key 'CompanyName' greater than {} characters".format(
                        self._str_max_len
                    )
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        data = {
            "name": self._destination["name"],
            "company": self._destination["company_name"],
            "address-details": AddressDetails(self._destination).data(),
        }

        if self._is_international:
            data["client-voice-number"] = self._destination["phone"]
        return data
