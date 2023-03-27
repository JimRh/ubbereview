"""
    Title: API Model
    Description: This file will contain functions for API Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import CharField, BooleanField

from api.globals.project import DEFAULT_CHAR_LEN, LETTER_MAPPING_LEN, API_API_CATEGORY
from api.models.base_table import BaseTable


class API(BaseTable):

    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    active = BooleanField(default=True)
    category = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=API_API_CATEGORY, default="NA")

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        if self.active:
            return f"< API ( {self.name} : Active) >"
        return f"< API ( {self.name} : Inactive) >"

    # Override
    def __str__(self) -> str:
        if self.active:
            return self.name + ": Active"
        return self.name + ": Inactive"
