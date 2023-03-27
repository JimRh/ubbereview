"""
    Title: Dispatch Model
    Description: This file will contain functions for Dispatch Model.
    Created: February 11, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Carrier, Contact
from api.models.base_table import BaseTable


class Dispatch(BaseTable):
    """
        Dispatch Model
    """

    carrier = ForeignKey(
        Carrier, on_delete=PROTECT, related_name='dispatch_carrier', help_text="Carrier Dispatches or Terminals"
    )
    contact = ForeignKey(
        Contact,
        on_delete=PROTECT,
        related_name='dispatch_contact',
        help_text="Contact for dispatch, contains request email"
    )
    location = CharField(max_length=DEFAULT_CHAR_LEN, help_text="City Name: Edmonton, Ottawa")
    is_default = BooleanField(default=False, help_text="Is the dispatch the default location.")

    class Meta:
        verbose_name = "Dispatch Number"
        verbose_name_plural = "RS: Dispatches"
        ordering = ["carrier", "location"]

    @classmethod
    def create(cls, param_dict: dict = None) -> 'Dispatch':
        """
            Create Dispatch from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Dispatch Object
        """

        dispatch = cls()
        if param_dict is not None:
            dispatch.set_values(param_dict)
            dispatch.carrier = param_dict.get("carrier")
            dispatch.contact = param_dict.get("contact")
        return dispatch

    @property
    def carrier_name(self) -> str:
        """
            Get Carrier Name
            :return: Name
        """

        return self.carrier.name

    @property
    def carrier_code(self) -> int:
        """
           Get Carrier Code
            :return: Code
        """
        return self.carrier.code

    @property
    def name(self) -> str:
        """
            Get Contact Name
            :return: Name
        """
        return self.contact.name

    @property
    def phone(self) -> str:
        """
            Get Contact Phone
            :return: Phone
        """

        return self.contact.phone

    @property
    def email(self) -> str:
        """
            Get Contact Email
            :return: Email
        """
        return self.contact.email

    # Override
    def __repr__(self) -> str:
        return f"< Dispatch ({self.carrier}, {self.location}, Default: {self.is_default}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier}, {self.location}, Default: {self.is_default}"
