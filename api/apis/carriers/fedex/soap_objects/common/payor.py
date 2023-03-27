from api.apis.carriers.fedex.soap_objects.common.party import Party
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class Payor(FedExSoapObject):
    _optional_keys = {"ResponsibleParty"}

    def __init__(self, payor_information: dict = None, account_number: str = ""):
        if payor_information:
            payor = Party(party_details=payor_information, is_payor=True).data
        else:
            payor = Party(
                {
                    "company_name": "BBE Expediting Ltd",
                    "phone": "",
                    "email": "",
                    "address": "1759 35 Ave E",
                    "city": "Edmonton International Airport",
                    "province": "AB",
                    "postal_code": "T9E0V6",
                    "country": "CA",
                },
                is_payor=True,
                account=account_number,
            ).data

        super().__init__({"ResponsibleParty": payor}, optional_keys=self._optional_keys)
