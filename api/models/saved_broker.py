"""
    Title: Saved Broker Model
    Description: This file will contain functions for Saved Brokers Model.
    Created: May 10, 2021
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import PROTECT, CASCADE
from django.db.models.fields.related import ForeignKey

from api.globals.project import MAX_CHAR_LEN, LETTER_MAPPING_LEN
from api.models import SubAccount, Address, Contact
from api.models.base_table import BaseTable


class SavedBroker(BaseTable):

    sub_account = ForeignKey(SubAccount, on_delete=PROTECT, help_text="The account the saved broker belongs to.")
    address = ForeignKey(Address, on_delete=CASCADE, blank=True, null=True, related_name='broker_address', help_text="Broker address information")
    contact = ForeignKey(Contact, on_delete=PROTECT, related_name='broker_contact', help_text="Broker contact information")

    class Meta:
        verbose_name = "Saved Broker"
        verbose_name_plural = "Saved Brokers"

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
            obj.sub_account = param_dict.get('sub_account')
            obj.address = param_dict.get('address')
            obj.contact = param_dict.get('contact')
        return obj

    # Override
    def __repr__(self) -> str:
        return f"< Saved Broker ({repr(self.sub_account)}: {repr(self.address)}, {repr(self.contact)}) >"

    # Override
    def __str__(self) -> str:
        return f"{str(self.sub_account)}: {self.address}, {self.contact}"
