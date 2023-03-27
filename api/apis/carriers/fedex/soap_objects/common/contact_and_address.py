from api.apis.carriers.fedex.soap_objects.common.address import Address
from api.apis.carriers.fedex.soap_objects.common.contact import Contact
from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject


class ContactAndAddress(FedExSoapObject):
    _optional_keys = {"Contact", "Address"}

    def __init__(self, party_details: dict):
        super().__init__(
            {
                "Contact": Contact(contact_details=party_details).data,
                "Address": Address(address_details=party_details).data,
            },
            optional_keys=self._optional_keys,
        )
