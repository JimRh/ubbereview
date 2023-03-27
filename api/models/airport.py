"""
    Title: Airport Model
    Description: This file will contain functions for Airport Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Address
from api.models.base_table import BaseTable


class Airport(BaseTable):

    address = ForeignKey(Address, null=True, on_delete=CASCADE, related_name='airport_address', blank=True)
    name = CharField(max_length=DEFAULT_CHAR_LEN)
    code = CharField(max_length=3, unique=True)

    class Meta:
        ordering = ["code"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Airport ({self.name}, {self.code}) >"

    # Override
    def __str__(self) -> str:
        return self.name + ", " + self.code
