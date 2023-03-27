"""
    Title: DangerousGoodExceptedQuantity Model
    Description: This file will contain functions for DangerousGoodExceptedQuantity Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.fields import PositiveSmallIntegerField, DecimalField

from api.globals.project import MAX_WEIGHT_DIGITS, BASE_TEN
from api.models.base_table import BaseTable


class DangerousGoodExceptedQuantity(BaseTable):
    """
        DangerousGoodExceptedQuantity
    """
    _sig_fig = Decimal(str(BASE_TEN ** (3 * -1)))

    excepted_quantity_code = PositiveSmallIntegerField(unique=True)
    inner_cutoff_value = DecimalField(
        decimal_places=3,
        max_digits=MAX_WEIGHT_DIGITS,
        help_text="0 indicates not permitted as excepted quantity. In KG/L"
    )
    outer_cutoff_value = DecimalField(
        decimal_places=3,
        max_digits=MAX_WEIGHT_DIGITS,
        help_text="0 indicates not permitted as excepted quantity. In KG/L"
    )

    class Meta:
        verbose_name = "Dangerous Good Excepted Quantity"
        verbose_name_plural = "Dangerous Good Excepted Quantities"
        ordering = ["excepted_quantity_code"]

    # Override
    def clean(self) -> None:
        if self.excepted_quantity_code > 5 or self.excepted_quantity_code < 0:
            raise ValidationError("Field 'excepted_quantity_code' must be from 0 to 5 inclusive")

    # Override
    def save(self, *args, **kwargs) -> None:
        self.inner_cutoff_value = self.inner_cutoff_value.quantize(self._sig_fig)
        self.outer_cutoff_value = self.outer_cutoff_value.quantize(self._sig_fig)

        self.clean_fields()
        self.clean()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< DangerousGoodExceptedQuantity (E{str(self.excepted_quantity_code)}) >"

    # Override
    def __str__(self) -> str:
        return f"E{str(self.excepted_quantity_code)}"
