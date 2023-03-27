from api.apis.carriers.fedex.soap_objects.common.web_authentication_credential import (
    WebAuthenticationCredential,
)
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class WebAuthenticationDetail(FedExSoapObject):
    _required_keys = {"UserCredential"}

    _optional_keys = {"ParentCredential"}

    def __init__(self, key, password):
        super().__init__(
            {
                "UserCredential": WebAuthenticationCredential(
                    key=key, password=password
                ).data
            },
            required_keys=self._required_keys,
            optional_keys=self._optional_keys,
        )
