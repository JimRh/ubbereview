from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class International(SOAPObj):
    def __init__(self, country_code) -> None:
        self._country_code = country_code

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {"country-code": self._country_code}
