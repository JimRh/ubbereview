"""
    Title: Saved Contact Model Class
    Description: This file will contain the Saved Contact model for the database.
    Created: Feb 8, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
from django.db.models import ForeignKey, PROTECT
from django.db.models.fields import CharField, BooleanField
from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Contact, SubAccount
from api.models.base_table import BaseTable

# TODO - Update username to user FK when once over


class SavedContact(BaseTable):
    """
    Save Contact Model.
    """

    account = ForeignKey(
        SubAccount,
        on_delete=PROTECT,
        help_text="The account the saved contact belongs to.",
    )
    username = CharField(
        max_length=DEFAULT_CHAR_LEN,
        help_text="Temp: Username field tell user is on api side",
    )
    contact_hash = CharField(
        max_length=DEFAULT_CHAR_LEN,
        help_text="Hash of all contact parts to check for duplicates",
        default="",
    )
    contact = ForeignKey(
        Contact,
        on_delete=PROTECT,
        related_name="saved_contact",
        help_text="Saved contact information",
    )
    is_origin = BooleanField(default=False, help_text="Is the contact only for origin?")
    is_destination = BooleanField(
        default=False, help_text="Is the contact only for destination?"
    )
    is_vendor = BooleanField(
        default=False, help_text="Is the contact a vendor contact?"
    )

    class Meta:
        verbose_name = "Saved Contact"
        verbose_name_plural = "Saved Contacts"
        ordering = ["account", "username"]

    @classmethod
    def create(cls, param_dict: dict = None):
        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.account = param_dict.get("account")
            obj.contact = param_dict["contact"]

        return obj

    # Override
    def __repr__(self) -> str:
        return f"< Saved Contact ({self.account}, {self.contact}, Origin {self.is_origin}, Destination {self.is_destination}"

    # Override
    def __str__(self) -> str:
        return f"{self.account}: {self.contact}, Origin: {self.is_origin}, Destination: {self.is_destination}"
