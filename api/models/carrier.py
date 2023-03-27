"""
    Title: Carrier Model
    Description: This file will contain functions for Carrier Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import CharField, DecimalField, BooleanField, EmailField, PositiveSmallIntegerField

from api.globals.project import DEFAULT_CHAR_LEN, PERCENTAGE_PRECISION, BASE_TEN, WEIGHT_PRECISION, MAX_WEIGHT_DIGITS, \
    LETTER_MAPPING_LEN, PRICE_PRECISION
from api.models import Airbase
from api.models.base_table import BaseTable


class Carrier(BaseTable):
    """
        Carrier Model
    """

    _percentage_sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))
    _weight_sig_fig = Decimal(str(BASE_TEN ** (WEIGHT_PRECISION * -1)))
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    _CARRIER_MODES = (
        ("AI", "Air"),
        ("CO", "Courier"),
        ("LT", "LTL"),
        ("FT", "FTL"),
        ("SE", "Sealift"),
        ("NA", "N/A")
    )

    _TYPES = (
        ("AP", "API"),
        ("RS", "Rate Sheet"),
        ("MC", "Manual Carrier"),
        ("NA", "N/A")
    )

    code = PositiveSmallIntegerField(unique=True, help_text="The internal carrier number")
    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    bc_vendor_code = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Must equal what the carrier vendor code  in bc", default="", blank=True
    )
    email = EmailField(blank=True)

    linear_weight = DecimalField(
        decimal_places=WEIGHT_PRECISION,
        max_digits=MAX_WEIGHT_DIGITS,
        default=Decimal("10.00"),
        help_text="The linear (length) cutoff until a new cost calculation is used"
    )

    mode = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_CARRIER_MODES, default="NA")
    type = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_TYPES, default="NA")
    is_kilogram = BooleanField(
        default=False,
        help_text="Does the carrier calculate dimensions and weight in imperial or metric. This is an internal "
                  "reference data attribute."
    )
    is_dangerous_good = BooleanField(default=False, help_text="Does the carrier ship dangerous goods")
    is_pharma = BooleanField(default=False, help_text="Does the carrier ship pharma goods")
    is_bbe_only = BooleanField(default=True, help_text="Is the carrier to be shown to BBE only?")
    is_allowed_account = BooleanField(default=True, help_text="Is the carrier allowed to be shown to accounts?")
    is_allowed_public = BooleanField(default=True, help_text="Is the carrier allowed to be shown to public?")

    class Meta:
        verbose_name = "Carrier"
        verbose_name_plural = "Carriers"
        ordering = ["name"]

    @classmethod
    def carrier_modes(cls):
        return cls._CARRIER_MODES

    @classmethod
    def system_type(cls):
        return cls._TYPES

    # Override
    def save(self, *args, **kwargs) -> None:
        self.linear_weight = self.linear_weight.quantize(self._weight_sig_fig)

        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

        try:
            Airbase.objects.get(code="", carrier=self)
        except ObjectDoesNotExist:
            Airbase.create({
                "code": "",
                "address": None,
                "carrier": self
            }).save()

    # Override
    def __repr__(self) -> str:
        return f"< Carrier ({self.name}: {self.code}) >"

    # Override
    def __str__(self) -> str:
        return self.name
