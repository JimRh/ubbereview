from typing import Union

from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class PaymentInfo(SOAPObj):
    def __init__(self, world_request: dict) -> None:
        self._world_request = world_request
        self._carrier_account = self._world_request["_carrier_account"]

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        return {"contract-id": self._carrier_account.contract_number.decrypt()}
