"""
    Title: Saved Address Model Class
    Description: This file will contain the Saved Address model for the database.
    Created: Jan 27, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import SubAccount, Address
from api.models.base_table import BaseTable


# TODO - Update username to user FK when once over


class SavedAddress(BaseTable):
    """
    Save Address Model.
    """

    account = ForeignKey(
        SubAccount,
        on_delete=PROTECT,
        help_text="The account the saved address belongs to.",
    )
    name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Address Nick Name.")
    username = CharField(
        max_length=DEFAULT_CHAR_LEN,
        help_text="Temp: Username field tell user is on api side",
    )
    address_hash = CharField(
        max_length=DEFAULT_CHAR_LEN,
        help_text="Hash of all address parts to check for duplicates",
        default="",
    )
    address = ForeignKey(
        Address,
        on_delete=PROTECT,
        related_name="saved_address",
        help_text="Saved address information",
    )
    is_origin = BooleanField(default=False, help_text="Is the address only for origin?")
    is_destination = BooleanField(
        default=False, help_text="Is the address only for destination?"
    )
    is_vendor = BooleanField(
        default=False, help_text="Is the address a vendor address?"
    )

    class Meta:
        verbose_name = "Saved Address"
        verbose_name_plural = "Saved Addresses"
        ordering = ["account", "username", "name"]

    @classmethod
    def create(cls, param_dict: dict = None):
        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.account = param_dict.get("account")
            obj.address = param_dict["address"]

        return obj

    # Override
    def __repr__(self) -> str:
        return f"< SavedAddress ({repr(self.account)}: {self.address}, Origin {self.is_origin}, Destination {self.is_destination}"

    # Override
    def __str__(self) -> str:
        return f"{str(self.account)}: {self.address}, Origin: {self.is_origin}, Destination: {self.is_destination}"
