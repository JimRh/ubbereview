"""
    Title: NatureOfGood Model
    Description: This file will contain functions for NatureOfGood Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, BooleanField, PositiveIntegerField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN, LETTER_MAPPING_LEN
from api.models.base_table import BaseTable
from api.models.cn_skyline_account import SkylineAccount


class NatureOfGood(BaseTable):
    """
        NatureOfGood Model
    """

    _NOG_TYPES = (
        ("DR", "Dry"),
        ("CO", "Cooler"),
        ("FR", "Frozen"),
        ("DG", "Dangerous Good"),
        ("OS", "Oversize")
    )

    skyline_account = ForeignKey(SkylineAccount, on_delete=CASCADE, related_name="nog_account")
    rate_priority_id = PositiveIntegerField(help_text="Rate priority identifier of the NOG")
    rate_priority_code = CharField(max_length=DEFAULT_CHAR_LEN)
    rate_priority_description = CharField(max_length=DEFAULT_CHAR_LEN)
    nog_id = PositiveIntegerField()
    nog_description = CharField(max_length=DEFAULT_CHAR_LEN)
    nog_type = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_NOG_TYPES, help_text="Cooler, Frozen, Dry, or DG")
    transit = PositiveIntegerField(default=0)
    is_food = BooleanField(default=False, help_text="Is the commodity Food?")

    class Meta:
        verbose_name = "Nature of Good"
        verbose_name_plural = "CN - Nature of Good's"

    # Override
    def __repr__(self) -> str:
        return f"< NatureOfGood ({self.skyline_account.skyline_account}, {self.rate_priority_id}, {self.nog_id}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.skyline_account.skyline_account}, {self.rate_priority_id}, {self.nog_id}"
