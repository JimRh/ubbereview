from api.apis.carriers.fedex.soap_objects.soap_object import FedExSoapObject
from api.apis.carriers.fedex.validation.validators import Name, Phone


class Contact(FedExSoapObject):
    _optional_keys = {
        "ContactId",
        "PersonName",
        "Title",
        "CompanyName",
        "PhoneNumber",
        "PhoneExtension",
        "TollFreePhoneNumber",
        "PagerNumber",
        "FaxNumber",
        "EMailAddress",
    }
    _validators = {
        "PersonName": Name,
        "CompanyName": Name,
        "PhoneNumber": Phone,
    }

    def __init__(self, contact_details: dict):
        super().__init__(optional_keys=self._optional_keys, validators=self._validators)

        name = contact_details.get("name")
        if name:
            self.add_value("PersonName", name)

        company_name = contact_details.get("company_name")
        if company_name:
            self.add_value("CompanyName", company_name)

        telephone = contact_details.get("phone")
        if telephone:
            self.add_value("PhoneNumber", telephone)

        email = contact_details.get("email")
        if email:
            self.add_value("EMailAddress", "customerservice@ubbe.com")
