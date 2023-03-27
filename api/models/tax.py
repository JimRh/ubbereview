"""
    Title: Tax Model
    Description: This file will contain functions for Tax Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db.models.deletion import CASCADE
from django.db.models.fields import DecimalField, DateTimeField
from django.db.models.fields.related import OneToOneField

from api.globals.project import PERCENTAGE_PRECISION, MAX_PERCENTAGE_DIGITS, BASE_TEN, PRICE_PRECISION
from api.models import Province
from api.models.base_table import BaseTable


class Tax(BaseTable):
    _sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    province = OneToOneField(Province, on_delete=CASCADE, related_name="tax_province")
    tax_rate = DecimalField(
        max_digits=MAX_PERCENTAGE_DIGITS,
        decimal_places=PERCENTAGE_PRECISION,
        help_text="Represented in whole percentage units. E.g. 15.55 = 15.55% tax."
    )
    expiry = DateTimeField()

    class Meta:
        ordering = ["province__name"]
        verbose_name_plural = "Taxes"

    @property
    def decimal(self) -> Decimal:
        return self.tax_rate / 100

    @property
    def decimal_plus(self) -> Decimal:
        return (self.tax_rate / 100) + 1

    # Override
    def save(self, *args, **kwargs) -> None:
        self.tax_rate = self.tax_rate.quantize(self._sig_fig)

        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Taxes ({repr(self.province)}: {self.tax_rate}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.province}: {self.tax_rate}"
