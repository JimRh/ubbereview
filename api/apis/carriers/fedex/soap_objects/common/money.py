from decimal import Decimal

from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class Money(FedExSoapObject):
    _required_keys = {"Currency", "Amount"}

    def __init__(self, amount: Decimal):
        super().__init__(
            {"Currency": "CAD", "Amount": amount}, required_keys=self._required_keys
        )
