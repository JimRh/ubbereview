"""
    Title: Middle Location Model
    Description: This file will contain functions for Middle Location Model.
    Created: March 1, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""


from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, BooleanField, EmailField
from django.db.models.fields.related import ForeignKey

from api.globals.project import AIRPORT_CODE_LEN
from api.models import Address
from api.models.base_table import BaseTable


class MiddleLocation(BaseTable):
    """
        Middle Location Model
    """
    # TODO - Add unqiue to code after private/public apis are done.

    address = ForeignKey(Address, on_delete=CASCADE, related_name='middle_location_address')
    code = CharField(max_length=AIRPORT_CODE_LEN, help_text="IATA Code for location")
    is_available = BooleanField(default=False, help_text="Is the location available?")
    email = EmailField(default="", help_text="Email to send notification to.")

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create Middle Location from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Middle Location Object
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.address = param_dict.get('address')
        return obj

    @property
    def get_ship_dict(self) -> dict:
        """
            Get address details for shipping in dictionary format.
            :return: dict of address details
        """

        ret = self.address.get_ship_dict
        ret["base"] = self.code
        ret["email"] = self.email
        return ret

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< MiddleLocation ({self.code}, {self.address.city}, {self.address.province.country.code}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.code}, {self.address.city}, {self.address.province.country.code}"
