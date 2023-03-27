"""
    Title: RateSheetLane Model
    Description: This file will contain functions for RateSheetLane Model.
    Created: February 6, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db.models.deletion import CASCADE
from django.db.models.fields import DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import PRICE_PRECISION, MAX_PRICE_DIGITS, BASE_TEN, WEIGHT_BREAK_PRECISION, \
    MAX_WEIGHT_BREAK_DIGITS
from api.models import RateSheet
from api.models.base_table import BaseTable


class RateSheetLane(BaseTable):
    """
        RateSheetLane Model
    """
    _wb_sig_fig = Decimal(str(BASE_TEN ** (WEIGHT_BREAK_PRECISION * -1)))
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    rate_sheet = ForeignKey(RateSheet, on_delete=CASCADE, related_name="rate_sheet_lane_rate_sheet")
    min_value = DecimalField(
        max_digits=MAX_WEIGHT_BREAK_DIGITS, decimal_places=WEIGHT_BREAK_PRECISION, default=Decimal("0.0000")
    )
    max_value = DecimalField(
        max_digits=MAX_WEIGHT_BREAK_DIGITS, decimal_places=WEIGHT_BREAK_PRECISION, default=Decimal("999999999999.9999")
    )
    cost = DecimalField(max_digits=MAX_PRICE_DIGITS, decimal_places=PRICE_PRECISION)

    class Meta:
        verbose_name = "Lane"
        verbose_name_plural = "RS: RateSheet Lanes"
        ordering = ["rate_sheet__carrier", "rate_sheet__origin_city", "rate_sheet__destination_city"]

    # Override
    def save(self, *args, **kwargs):
        self.min_value = self.min_value.quantize(self._wb_sig_fig)
        self.max_value = self.max_value.quantize(self._wb_sig_fig)
        self.cost = self.cost.quantize(self._price_sig_fig)

        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< RateSheetLane ({self.min_value} {self.max_value} RateCost: ${self.cost} ({self.rate_sheet.id})) >"

    # Override
    def __str__(self) -> str:
        return f"{self.min_value} {self.max_value} RateCost: ${self.cost} ({self.rate_sheet.id})"
