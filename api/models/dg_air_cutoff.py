"""
    Title: DangerousGoodAirCutoff Model
    Description: This file will contain functions for DangerousGoodAirCutoff Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import LETTER_MAPPING_LEN, BASE_TEN
from api.models import DangerousGoodPackingInstruction
from api.models.base_table import BaseTable


class DangerousGoodAirCutoff(BaseTable):
    """
        DangerousGoodAirCutoff Model
    """
    _sig_fig = Decimal(str(BASE_TEN ** (1 * -1)))
    _CUTOFF_TYPES = (
        ("L", "Limited"),
        ("P", "Passenger"),
        ("C", "Cargo"),
    )

    cutoff_value = DecimalField(
        decimal_places=1,
        max_digits=4,
        default=Decimal("0.0"),
        help_text="0 indicates forbidden. In KG/L"
    )
    packing_instruction = ForeignKey(
        DangerousGoodPackingInstruction,
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="dangerousgood_air_cutoff_packing_instricution"
    )
    type = CharField(max_length=LETTER_MAPPING_LEN, choices=_CUTOFF_TYPES)

    class Meta:
        verbose_name = "Dangerous Good Air Cutoff"
        ordering = ["packing_instruction__code", "cutoff_value"]
        unique_together = ("cutoff_value", "packing_instruction")

    # Override
    def save(self, *args, **kwargs) -> None:
        self.cutoff_value = self.cutoff_value.quantize(self._sig_fig)

        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodAirCutoff (PI {self.packing_instruction.code}: {self.cutoff_value} " \
            f"{self.get_type_display()}) >"

    # Override
    def __str__(self) -> str:
        return f"PI {self.packing_instruction.code}: {self.cutoff_value} {self.get_type_display()}"
