"""
    Title: Surcharge Model
    Description: This file will contain functions for Surcharge Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import MAX_CHAR_LEN, PRICE_PRECISION, MAX_PERCENTAGE_DIGITS, MAX_PRICE_DIGITS, \
    PERCENTAGE_PRECISION, BASE_TEN
from api.models.base_table import BaseTable


class Surcharge(BaseTable):
    """
        Surcharge Model
    """
    _cost_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _percentage_sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))

    name = CharField(max_length=MAX_CHAR_LEN)
    base_cost = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    cost = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In Account Currency.")
    percentage = DecimalField(decimal_places=PERCENTAGE_PRECISION, max_digits=MAX_PERCENTAGE_DIGITS)
    leg = ForeignKey("Leg", on_delete=CASCADE, related_name="surcharge_leg")

    class Meta:
        verbose_name = "Surcharge"
        verbose_name_plural = "Shipment - Surcharges"
        ordering = ["name"]

    def to_json(self) -> dict:
        """
            Get Surcharge as a dict
            :return: Surcharge dict
        """

        if self.percentage > Decimal("0.00"):
            surcharge_type = "Percentage"
        else:
            surcharge_type = "Flat Amount"

        return {
            "name": self.name,
            "cost": self.cost,
            "type": surcharge_type,
            "percentage": self.percentage
        }

    # Override
    def save(self, *args, **kwargs) -> None:
        self.cost = self.cost.quantize(self._cost_sig_fig)
        self.percentage = self.percentage.quantize(self._percentage_sig_fig)
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Surcharges ({self.name}: {self.cost}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.name}: {self.cost}"
