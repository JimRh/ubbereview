"""
    Title: BillOfLading (IE: BOL) Model
    Description: This file will contain functions for BillOfLading (IE: BOL) Model.
    Created: February 6, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Dispatch
from api.models.base_table import BaseTable


class BillOfLading(BaseTable):
    """
        BillOfLading (IE: BOL) Model
    """

    dispatch = ForeignKey(
        Dispatch, on_delete=PROTECT, related_name='bol_dispatch', help_text="Carrier Dispatch the BOl belongs to."
    )
    bill_of_lading = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Carrier Bill of Lading (BOL) Number")
    is_available = BooleanField(default=True, help_text="Is the bol available?")

    class Meta:
        verbose_name = "BillOfLading"
        verbose_name_plural = "RS: Bill Of Ladings"
        ordering = ["dispatch"]

    @classmethod
    def create(cls, param_dict: dict = None) -> 'BillOfLading':
        """
            Create Dispatch from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Dispatch Object
        """

        bol = cls()
        if param_dict is not None:
            bol.set_values(param_dict)
            bol.dispatch = param_dict.get("dispatch")
        return bol

    @property
    def dispatch_carrier(self) -> str:
        """
            Get Carrier Name
            :return: Carrier Name
        """

        return self.dispatch.carrier_name

    @property
    def dispatch_location(self) -> str:
        """
            Get dispatch location
            :return: location
        """

        return self.dispatch.location

    # Override
    def __repr__(self) -> str:
        return f"< BillOfLading ({self.dispatch}, {self.bill_of_lading}, {self.is_available}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.dispatch}, {self.bill_of_lading}, {self.is_available}"
