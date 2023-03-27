import copy
import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.parcel_chracteristics import (
    ParcelCharacteristics,
)
from api.apis.carriers.canada_post.soap_objects.rating_destination import (
    RatingDestination,
)
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class MailingScenario(SOAPObj):
    def __init__(self, world_request: dict) -> None:
        self._world_request = world_request
        self._carrier_account = self._world_request["_carrier_account"]
        self._customer_number = self._carrier_account.account_number.decrypt()
        self._contract_id = self._carrier_account.contract_number.decrypt()
        del self._world_request["_carrier_account"]
        self._parcel_characteristics = ParcelCharacteristics(
            world_request["package"]
        ).data()
        self._origin_postal_code = copy.deepcopy(world_request["origin"]["postal_code"])
        self._destination = RatingDestination(world_request["destination"]).data()
        self._clean()

    # Override
    def _clean(self) -> None:
        country_code = self._world_request["origin"]["country"].upper()
        self._origin_postal_code = self._origin_postal_code.replace(" ", "").upper()

        if country_code in {"CA", "US"}:
            if (
                re.fullmatch(POSTAL_CODE_REGEX[country_code], self._origin_postal_code)
                is None
            ):
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.MailingScenario": "Destination key 'PostalCode' does not match {}".format(
                            POSTAL_CODE_REGEX[country_code]
                        )
                    }
                )
        else:
            if len(self._origin_postal_code) > 14:
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.MailingScenario": "Destination key 'PostalCode' greater than "
                        "14 characters"
                    }
                )

    # Override
    def data(self) -> Union[list, dict]:
        return {
            "customer-number": self._customer_number,
            "contract-id": self._contract_id,
            "quote-type": "commercial",
            "parcel-characteristics": self._parcel_characteristics,
            "origin-postal-code": self._origin_postal_code,
            "destination": self._destination,
        }
