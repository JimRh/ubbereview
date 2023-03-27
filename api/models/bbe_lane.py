"""
    Title: BBE Lane Model
    Description: This file will contain functions for BBE Lane Model.
    Created: April 28, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re
from decimal import Decimal

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, DecimalField, IntegerField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.globals.project import PRICE_PRECISION, BASE_TEN, DEFAULT_CHAR_LEN, MAX_PRICE_DIGITS, DEFAULT_STRING_REGEX
from api.models import Carrier, Province
from api.models.base_table import BaseTable


class BBELane(BaseTable):
    """
        BBELane Model
    """

    _sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name="bbe_lane_carrier")
    service_code = CharField(max_length=DEFAULT_CHAR_LEN, default="ST")
    service_name = CharField(max_length=DEFAULT_CHAR_LEN, default="Standard")
    origin_city = CharField(max_length=DEFAULT_CHAR_LEN)
    origin_province = ForeignKey(Province, on_delete=CASCADE, related_name="bbe_lane_origin_province")
    origin_postal_code = CharField(max_length=DEFAULT_CHAR_LEN)
    destination_city = CharField(max_length=DEFAULT_CHAR_LEN)
    destination_province = ForeignKey(Province, on_delete=CASCADE, related_name="bbe_lane_destination_province")
    destination_postal_code = CharField(max_length=DEFAULT_CHAR_LEN)
    minimum_charge = DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_PRECISION,
        help_text="In CAD. Min cost for the lane."
    )

    weight_break = DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_PRECISION,
        help_text="Weight Break to go to price per weight. IE: Weight Break is 46,  Weight = 30, min is "
                  "used. weight is 50, price per is used. (50 * 0.65)"
    )
    price_per = DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="Price per metric or imperial, determined off of is metric flag."
    )
    transit_days = IntegerField(default=-1)
    is_metric = BooleanField(default=False, help_text="Is the lane priced in metric?")

    class Meta:
        verbose_name = "BBE Lane"
        verbose_name_plural = "BBE: Lane"

    @staticmethod
    def clean_city(city: str) -> str:
        return re.sub(DEFAULT_STRING_REGEX, '', city).lower()

    # Override
    def save(self, *args, **kwargs):
        self.price_per = self.price_per.quantize(self._sig_fig)
        self.minimum_charge = self.minimum_charge.quantize(self._sig_fig)
        self.weight_break = self.weight_break.quantize(self._sig_fig)

        self.origin_city = self.clean_city(self.origin_city)
        self.destination_city = self.clean_city(self.destination_city)

        self.clean_fields()

        if self.transit_days == "None":
            self.transit_days = -1

        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< BBELane ({self.service_name}, {self.origin_city}, {self.origin_postal_code}, " \
            f"{self.destination_city}, {self.destination_postal_code}, {self.minimum_charge}, {self.weight_break}, " \
            f"{self.price_per}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.service_name}, {self.origin_city}, {self.origin_postal_code}, {self.destination_city}, " \
            f"{self.destination_postal_code}"
