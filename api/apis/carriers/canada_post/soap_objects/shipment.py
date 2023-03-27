import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.delivery_spec import DeliverySpec
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj
from api.globals.project import POSTAL_CODE_REGEX


class Shipment(SOAPObj):
    def __init__(self, world_request: dict, order_number: str):
        self._world_request = world_request
        self._order_number = order_number
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._order_number) > 32:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Shipment": "tag 'groups-id' cannot be greater than 32 characters"
                }
            )

        if (
            re.fullmatch(
                POSTAL_CODE_REGEX["CA"], self._world_request["origin"]["postal_code"]
            )
            is None
        ):
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.Shipment": "Origin key 'PostalCode' does not match "
                    + POSTAL_CODE_REGEX["CA"]
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        postal_code = self._world_request["origin"]["postal_code"]

        return {
            "group-id": self._order_number,
            "cpc-pickup-indicator": True,
            "requested-shipping-point": postal_code.replace(" ", ""),
            "delivery-spec": DeliverySpec(
                self._world_request, self._order_number
            ).data(),
        }
