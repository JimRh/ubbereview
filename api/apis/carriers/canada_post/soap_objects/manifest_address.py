from typing import Union

from api.apis.carriers.canada_post.soap_objects.address_details import AddressDetails
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class ManifestAddress(SOAPObj):
    def __init__(self, address: dict) -> None:
        self._address = address

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "manifest-company": "BBE EXPEDITING LTD",
            "phone-number": "7808906893",
            "address-details": AddressDetails(self._address).data(),
        }
