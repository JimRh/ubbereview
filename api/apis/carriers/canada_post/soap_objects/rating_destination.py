from typing import Union

from api.apis.carriers.canada_post.soap_objects.domestic import Domestic
from api.apis.carriers.canada_post.soap_objects.international import International
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.apis.carriers.canada_post.soap_objects.united_states import UnitedStates


class RatingDestination(SOAPObj):
    def __init__(self, destination: dict) -> None:
        self._destination = destination
        self._country_code = destination["country"].upper()

        if self._country_code == "CA":
            self._is_domestic = True
            self._is_united_states = False
        elif self._country_code == "US":
            self._is_domestic = False
            self._is_united_states = True
        else:
            self._is_domestic = False
            self._is_united_states = False

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        postal_code = self._destination["postal_code"]

        if self._is_domestic:
            return {"domestic": Domestic(postal_code).data()}
        if self._is_united_states:
            return {"united-states": UnitedStates(postal_code).data()}
        return {"international": International(self._country_code).data()}
