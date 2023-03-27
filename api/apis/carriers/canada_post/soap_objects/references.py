from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class References(SOAPObj):
    def __init__(self, order_number: str, awb: str = None) -> None:
        self._order_number = order_number
        self._awb = awb
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._order_number) > 35:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.References": "OrderNumber greater than 35 characters"
                }
            )

        if self._awb is not None:
            if len(self._awb) > 35:
                raise CanadaPostAPIException(
                    {
                        "api.error.canada_post.SOAPObj.References": "AWB greater than 35 characters"
                    }
                )

    # Override
    def data(self) -> Union[list, dict]:
        if self._awb is not None:
            return {"customer-ref-1": self._order_number, "customer-ref-2": self._awb}
        return {"customer-ref-1": self._order_number}
