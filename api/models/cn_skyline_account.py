"""
    Title: SkylineAccount Model
    Description: This file will contain functions for SkylineAccount Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, BooleanField, IntegerField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import SubAccount
from api.models.base_table import BaseTable


class SkylineAccount(BaseTable):
    """
        SkylineAccount Model
    """

    sub_account = ForeignKey(SubAccount, on_delete=CASCADE)
    skyline_account = CharField(max_length=DEFAULT_CHAR_LEN)
    customer_id = IntegerField()

    class Meta:
        verbose_name = "Skyline Account"
        verbose_name_plural = "CN - Skyline Account's"

    # Override
    def __repr__(self) -> str:
        return f"< SkylineAccount ({self.sub_account}, {self.skyline_account}, {self.customer_id}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.sub_account}: {self.skyline_account}, {self.customer_id}"
