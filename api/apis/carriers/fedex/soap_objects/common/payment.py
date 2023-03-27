from api.apis.carriers.fedex.globals.globals import PAYMENT_TYPE
from api.apis.carriers.fedex.soap_objects.common.payor import Payor
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class Payment(FedExSoapObject):
    _optional_keys = {"PaymentType", "Payor"}

    def __init__(
        self,
        payor_information: dict = None,
        intl_duties: bool = False,
        account_number: str = "",
    ):
        if intl_duties:
            super().__init__(
                {"PaymentType": "RECIPIENT"}, optional_keys=self._optional_keys
            )
        else:
            super().__init__(
                {
                    "PaymentType": PAYMENT_TYPE,
                    "Payor": Payor(
                        payor_information=payor_information,
                        account_number=account_number,
                    ).data,
                },
                optional_keys=self._optional_keys,
            )
