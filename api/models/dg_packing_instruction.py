"""
    Title: DangerousGoodPackingInstruction Model
    Description: This file will contain functions for DangerousGoodPackingInstruction Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import PositiveSmallIntegerField, CharField
from django.db.models.fields.related import ManyToManyField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import DangerousGoodPackagingType
from api.models.base_table import BaseTable


class DangerousGoodPackingInstruction(BaseTable):
    """
        DangerousGoodPackingInstruction Model
    """

    code = PositiveSmallIntegerField(unique=True)
    packaging_types = ManyToManyField(
        DangerousGoodPackagingType,
        blank=True,
        related_name="dangerousgoodairpackinginstruction_packaging_types",
        help_text="Acceptable packaging types, blank indicates any."
    )
    exempted_statement = CharField(max_length=DEFAULT_CHAR_LEN, blank=True)

    class Meta:
        verbose_name = "Dangerous Good Air Packing Instruction"
        ordering = ["code"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodPackingInstruction ({str(self.code)}) >"

    # Override
    def __str__(self) -> str:
        return str(self.code)
