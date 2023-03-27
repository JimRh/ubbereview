"""
    Title: NorthernPDAddress Model
    Description: This file will contain functions for NorthernPDAddress Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db.models.fields import CharField, PositiveSmallIntegerField, DecimalField

from api.globals.project import DEFAULT_CHAR_LEN, WEIGHT_PRECISION, PRICE_PRECISION, BASE_TEN, MAX_PRICE_DIGITS, \
    MAX_WEIGHT_DIGITS
from api.models.base_table import BaseTable


class NorthernPDAddress(BaseTable):
    """
        NorthernPDAddress Model
    """
    _weight_sig_fig = Decimal(str(BASE_TEN ** (WEIGHT_PRECISION * -1)))
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    pickup_id = PositiveSmallIntegerField(help_text="The identifier of the address for pickup")
    delivery_id = PositiveSmallIntegerField(help_text="The identifier of the address for delivery")
    city_name = CharField(max_length=DEFAULT_CHAR_LEN)
    price_per_kg = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS)
    min_price = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="The shipment flat fee"
    )
    cutoff_weight = DecimalField(
        decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS, help_text="The max weight")

    class Meta:
        verbose_name = "Northern PD Address"
        verbose_name_plural = "CN - Northern PD Addresses"
        ordering = ["city_name"]

    # Override
    def save(self, *args, **kwargs):
        self.price_per_kg = self.price_per_kg.quantize(self._price_sig_fig)
        self.min_price = self.min_price.quantize(self._price_sig_fig)
        self.cutoff_weight = self.cutoff_weight.quantize(self._weight_sig_fig)

        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< NorthernPDAddress ({self.city_name}, {self.price_per_kg}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.city_name}, {self.price_per_kg}"
