"""
    Title: API Permissions Model
    Description: This file will contain functions for API Permissions Model.
    Created: February 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import CharField, BooleanField

from api.globals.project import DEFAULT_CHAR_LEN, LETTER_MAPPING_LEN, API_API_CATEGORY, MAX_CHAR_LEN
from api.models.base_table import BaseTable


class ApiPermissions(BaseTable):

    name = CharField(max_length=DEFAULT_CHAR_LEN)
    permissions = CharField(max_length=DEFAULT_CHAR_LEN)
    category = CharField(
        max_length=LETTER_MAPPING_LEN * 2, choices=API_API_CATEGORY, default="NA", help_text="Api Category"
    )
    reason = CharField(max_length=MAX_CHAR_LEN, default="", blank=True, null=True, help_text="Reason why api is off.")
    is_active = BooleanField(default=True, help_text="Is the api active?")
    is_admin = BooleanField(default=True, help_text="Is the api admin only endpoint?")

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "permissions")

    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        if self.is_active:
            return f"< ApiPermissions ( {self.name} : Active) >"
        return f"< ApiPermissions ( {self.name} : Inactive) >"

    # Override
    def __str__(self) -> str:
        if self.is_active:
            return self.name + ": Active"
        return self.name + ": Inactive"
