"""
    Title: DangerousGoodGenericLabel Model
    Description: This file will contain functions for DangerousGoodGenericLabel Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import CharField, PositiveSmallIntegerField
from django.db.models.fields.files import ImageField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models.base_table import BaseTable


class DangerousGoodGenericLabel(BaseTable):
    """
        DangerousGoodGenericLabel Model
    """

    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    width = PositiveSmallIntegerField(help_text="Measured in mm.")
    height = PositiveSmallIntegerField(help_text="Measured in mm.")
    label = ImageField(unique=True, upload_to="Assets/DangerousGoods/Labels/Generic", help_text="Relative image path")

    class Meta:
        verbose_name = "Dangerous Good Generic Label"
        ordering = ["name"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodGenericLabel ({self.name}) >"

    # Override
    def __str__(self) -> str:
        return self.name
