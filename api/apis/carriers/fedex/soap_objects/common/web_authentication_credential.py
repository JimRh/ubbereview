from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class WebAuthenticationCredential(FedExSoapObject):
    _required_keys = {"Key", "Password"}

    def __init__(self, key, password):
        super().__init__(
            {"Key": key, "Password": password}, required_keys=self._required_keys
        )
