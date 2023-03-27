"""
    Title: DangerousGoodPackingGroup Model
    Description: This file will contain functions for DangerousGoodPackingGroup Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models.fields import CharField

from api.globals.project import LETTER_MAPPING_LEN, DEFAULT_CHAR_LEN
from api.models.base_table import BaseTable


class DangerousGoodPackingGroup(BaseTable):
    """
        DangerousGoodPackingGroup
    """

    _PACKING_GROUPS = (
        ("0", "N/A"),
        ("1", "I"),
        ("2", "II"),
        ("3", "III")
    )

    packing_group = CharField(max_length=LETTER_MAPPING_LEN, choices=_PACKING_GROUPS, unique=True)
    description = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)

    class Meta:
        verbose_name = "Dangerous Good Packing Group"
        ordering = ["packing_group"]

    @property
    def packing_group_str(self):
        return self.get_packing_group_display()

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodPackingGroup ({self.get_packing_group_display()}: {self.description}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.get_packing_group_display()}: {self.description}"
