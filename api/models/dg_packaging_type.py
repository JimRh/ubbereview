"""
    Title: DangerousGoodPackagingType Model
    Description: This file will contain functions for DangerousGoodPackagingType Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models.fields import CharField

from api.globals.project import LETTER_MAPPING_LEN, DEFAULT_CHAR_LEN
from api.models.base_table import BaseTable


class DangerousGoodPackagingType(BaseTable):
    """
        DangerousGoodPackagingType Model
    """

    _PACKAGING_TYPES = (
        ("B", "Box"),
        ("D", "Drum"),
        ("J", "Jerrycan"),
        ("A", "Bag")
    )
    _MATERIALS = (
        ("ST", "Steel"),
        ("AL", "Aluminium"),
        ("ME", "Metal"),
        ("PW", "Plywood"),
        ("FI", "Fibre"),
        ("NA", "Natural Wood"),
        ("RE", "Reconstituted Wood"),
        ("FB", "Fibreboard"),
        ("TE", "Textile"),
        ("PA", "Paper"),
        ("PL", "Plastic"),
        ("CO", "Composite")
    )

    packaging_type = CharField(max_length=LETTER_MAPPING_LEN, choices=_PACKAGING_TYPES)
    material = CharField(max_length=2, choices=_MATERIALS)
    details = CharField(max_length=DEFAULT_CHAR_LEN, blank=True)
    code = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)

    class Meta:
        verbose_name = "Dangerous Good Packaging Type"
        ordering = ["material", "packaging_type"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.code = self.code.upper()

        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodPackagingType ({self.get_packaging_type_display()}: {self.get_material_display()} " \
            f"{self.code}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.get_packaging_type_display()}: {self.get_material_display()} {self.code}"
