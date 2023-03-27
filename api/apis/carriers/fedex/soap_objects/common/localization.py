from api.apis.carriers.fedex.globals.globals import ENGLISH, CANADA_ENGLISH
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class Localization(FedExSoapObject):
    _optional_keys = {"LanguageCode", "LocaleCode"}

    def __init__(self):
        super().__init__(
            {"LanguageCode": ENGLISH, "LocaleCode": CANADA_ENGLISH},
            optional_keys=self._optional_keys,
        )
