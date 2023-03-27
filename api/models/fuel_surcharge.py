"""
    Title: FuelSurcharge Model
    Description: This file will contain functions for FuelSurcharge Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.core.validators import RegexValidator
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN, PERCENTAGE_PRECISION, MAX_PERCENTAGE_DIGITS, LETTER_MAPPING_LEN, \
    BASE_TEN
from api.models import Carrier
from api.models.base_table import BaseTable


class FuelSurcharge(BaseTable):
    """
        FuelSurcharge Model
    """

    _sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))
    _hundred = Decimal("100.00")
    _FUEL_TYPES = (
        ("D", "Domestic"),
        ("I", "International")
    )
    daterange_validator = RegexValidator(
        regex=r'[2-9]\d{3}-[0-1]\d-[0-3]\d:[2-9]\d{3}-[0-1]\d-[0-3]\d', message="Updated date not valid format"
    )

    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name='fuel_surcharge_carrier')
    fuel_type = CharField(max_length=LETTER_MAPPING_LEN, choices=_FUEL_TYPES, default="D")
    updated_date = CharField(
        max_length=DEFAULT_CHAR_LEN,
        blank=True,
        validators=[daterange_validator],
        help_text="A daterange indicating the valid dates for the surcharges"
    )
    ten_thou_under = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="This field is measured in pounds (lbs)"
    )
    ten_thou_to_fifty_five_thou = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="This field is measured in pounds (lbs)"
    )
    fifty_five_thou_greater = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="This field is measured in pounds (lbs)"
    )

    class Meta:
        verbose_name = "Fuel Surcharge"
        verbose_name_plural = "Fuel Surcharges"
        ordering = ["carrier", "fuel_type"]

    def get_json(self, weight: Decimal, freight_cost: Decimal) -> dict:
        """
            Get Fuel Surcharge information
            :param weight: Weight in Pounds
            :param freight_cost: Freight Cost
            :return: Charge Amount
        """

        if weight < Decimal("0.00"):
            raise ValueError("Weight must be a positive number")
        if weight < 10000:
            amount = ((self.ten_thou_under / self._hundred) * freight_cost).quantize(self._sig_fig)
            percentage = self.ten_thou_under
        elif weight < 55000:
            amount = ((self.ten_thou_to_fifty_five_thou / self._hundred) * freight_cost).quantize(self._sig_fig)
            percentage = self.ten_thou_to_fifty_five_thou
        else:
            amount = ((self.fifty_five_thou_greater / self._hundred) * freight_cost).quantize(self._sig_fig)
            percentage = self.fifty_five_thou_greater

        if not self.updated_date:
            date_range = ('', '')
        else:
            date_range = self.updated_date.split(':')

        return {
            "name": "Fuel Surcharge",
            "carrier_id": self.carrier.code,
            "cost": amount,
            "fuel_type": self.fuel_type,
            "percentage": percentage,
            "valid_to": date_range[1],
            "valid_from": date_range[0]
        }

    # Override
    def save(self, *args, **kwargs):
        self.ten_thou_under = self.ten_thou_under.quantize(self._sig_fig)
        self.ten_thou_to_fifty_five_thou = self.ten_thou_to_fifty_five_thou.quantize(self._sig_fig)
        self.fifty_five_thou_greater = self.fifty_five_thou_greater.quantize(self._sig_fig)

        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< FuelSurcharge ({self.carrier.name}, {self.get_fuel_type_display()}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier.name}, {self.get_fuel_type_display()}"
