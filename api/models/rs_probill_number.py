"""
    Title: ProBillNumber Model
    Description: This file will contain functions for ProBillNumber Model.
    Created: February 6, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Carrier
from api.models.base_table import BaseTable


class ProBillNumber(BaseTable):
    """
        ProBillNumber Model
    """

    carrier = ForeignKey(Carrier, on_delete=PROTECT, related_name='probillnumber_carrier')
    # TODO: Unique?
    probill_number = CharField(max_length=DEFAULT_CHAR_LEN, help_text="AKA: Bill of Lading (BOL)")
    available = BooleanField(default=True)

    class Meta:
        verbose_name = "ProBill Number"
        verbose_name_plural = "ProBill Numbers"
        ordering = ["carrier"]

    # Override
    def __repr__(self) -> str:
        return f"< ProBillNumber ({self.probill_number}) >"

    # Override
    def __str__(self) -> str:
        return self.probill_number
