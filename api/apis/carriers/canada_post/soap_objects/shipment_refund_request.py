import re
from typing import Union

from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class ShipmentRefundRequest(SOAPObj):
    def __init__(self, email: str) -> None:
        self._email = email
        self._clean()

    # Override
    def _clean(self) -> None:
        if len(self._email) > 60:
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ShipmentRefundRequest": "Shipment Refund Request key 'Email' greater "
                    "than 60 characters"
                }
            )

        if (
            re.fullmatch(
                r"(['\w\-+]+)(\.['\w\-+]+)*@([A-Za-z\d\-]+)(\.[A-Za-z\d\-]+)*(\.[A-Za-z]{2,5})",
                self._email,
            )
            is None
        ):
            raise CanadaPostAPIException(
                {
                    "api.error.canada_post.SOAPObj.ShipmentRefundRequest": r"Shipment Refund Request key 'Email' does not match "
                    r"'(['\w\-+]+)(\.['\w\-+]+)*@([A-Za-z\d\-]+)(\.[A-Za-z\d\-]+)*(\.[A-Za-z]{2,5})'"
                }
            )

    # Override
    def data(self) -> Union[list, dict]:
        return {"email": self._email}
