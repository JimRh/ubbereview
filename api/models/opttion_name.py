"""
    Title: OptionName Model
    Description: This file will contain functions for OptionName Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import CharField, BooleanField

from api.globals.project import DEFAULT_CHAR_LEN, MAX_CHAR_LEN
from api.models.base_table import BaseTable


class OptionName(BaseTable):
    """
        OptionName Model
    """

    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    description = CharField(max_length=MAX_CHAR_LEN)
    is_mandatory = BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "Option Name"
        verbose_name_plural = "Option - Option Names"

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< OptionName ({self.name}: {self.description}) >"

    # Override
    def __str__(self) -> str:
        return self.name
