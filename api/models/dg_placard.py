"""
    Title: DangerousGoodPlacard Model
    Description: This file will contain functions for DangerousGoodPlacard Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re

from django.core.exceptions import ValidationError
from django.db.models.fields import CharField
from django.db.models.fields.files import ImageField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models.base_table import BaseTable


class DangerousGoodPlacard(BaseTable):
    """
        DangerousGoodPlacard Model
    """

    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    background_rgb = CharField(max_length=DEFAULT_CHAR_LEN,
                                      help_text="The placard background RGB for the id winglet")
    font_rgb = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The placard font RGB for the id winglet")
    label = ImageField(unique=True, upload_to="Assets/DangerousGoods/Placards/", help_text="Relative image path")

    class Meta:
        verbose_name = "Dangerous Good Placard"

    # Override
    def clean(self) -> None:
        rgb_regex = r'([0-2][0-9]{0,2},[0-2][0-9]{0,2},[0-2][0-9]{0,2})'

        if re.fullmatch(rgb_regex, self.background_rgb) is None:
            raise ValidationError("Field 'background_rgb' must be format: " + rgb_regex)

        if re.fullmatch(rgb_regex, self.font_rgb) is None:
            raise ValidationError("Field 'font_rgb' must be format: " + rgb_regex)

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.clean()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodPlacard ({self.name}) >"

    # Override
    def __str__(self) -> str:
        return self.name
