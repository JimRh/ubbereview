"""
    Title: RateSheet Model
    Description: This file will contain functions for RateSheet Model.
    Created: February 6, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import re
from decimal import Decimal
from datetime import datetime

from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields import BooleanField, CharField, IntegerField, DecimalField, DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone

from api.globals.project import DEFAULT_CHAR_LEN, PRICE_PRECISION, LETTER_MAPPING_LEN, MAX_PRICE_DIGITS, \
    DEFAULT_STRING_REGEX, BASE_TEN, CURRENCY_CODE_LEN
from api.models import Province, Carrier, SubAccount
from api.models.base_table import BaseTable


class RateSheet(BaseTable):
    """
        RateSheet Model

        Air type does not work
    """

    _sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _TYPES = (
        ("AI", "Air"),
        ("LT", "LTL"),
        ("FT", "FTL"),
        ("CO", "Courier"),
        ("SE", "Sealift")
    )

    _RS_TYPES = (
        ("PHP", "Per Hundred Pounds"),
        ("PPO", "Per Pound"),
        ("PRT", "Per Revenue Ton"),
        ("PQA", "Per Quantity"),
        ("FLR", "Flat Rate")
    )

    sub_account = ForeignKey(SubAccount, on_delete=PROTECT, null=True)
    rs_type = CharField(max_length=LETTER_MAPPING_LEN * 3, choices=_RS_TYPES, default="PHP")
    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name="rate_sheet_carrier")
    upload_date = DateTimeField(
        help_text="Date the lane was uploaded.", default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    expiry_date = DateTimeField(
        help_text="Date the lane expires.", default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    origin_province = ForeignKey(Province, on_delete=CASCADE, related_name="rate_sheet_origin_province")
    destination_province = ForeignKey(Province, on_delete=CASCADE, related_name="rate_sheet_destination_province")
    origin_city = CharField(max_length=DEFAULT_CHAR_LEN)
    destination_city = CharField(max_length=DEFAULT_CHAR_LEN)
    currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Rate Sheet Currency")
    minimum_charge = DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_PRECISION,
        help_text="In CAD. Min cost for the lane."
    )
    maximum_charge = DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_PRECISION,
        help_text="In CAD. Max cost for the lane.",
        default=Decimal("0")
    )
    cut_off_time = CharField(
        max_length=DEFAULT_CHAR_LEN, default="13:30", help_text="Cut off time for same day pickup, EX: 14:00.")
    transit_days = IntegerField(default=-1)
    service_code = CharField(max_length=DEFAULT_CHAR_LEN, default="General")
    service_name = CharField(max_length=DEFAULT_CHAR_LEN, default="General")
    availability = CharField(
        max_length=DEFAULT_CHAR_LEN,
        blank=True,
        help_text="A string representing a custom freight forwarding day availability"
    )

    class Meta:
        verbose_name = "Rate Sheet"
        verbose_name_plural = "RS: Rate Sheets"

    @staticmethod
    def clean_city(city: str) -> str:
        return re.sub(DEFAULT_STRING_REGEX, '', city).title()

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create Middle Location from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Middle Location Object
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.sub_account = param_dict.get('sub_account')
            obj.carrier = param_dict.get('carrier')
            obj.origin_province = param_dict.get('origin_province')
            obj.destination_province = param_dict.get('destination_province')
        return obj

    def save(self, *args, **kwargs) -> None:
        self.origin_city = self.clean_city(self.origin_city)
        self.destination_city = self.clean_city(self.destination_city)
        self.minimum_charge = self.minimum_charge.quantize(self._sig_fig)
        self.upload_date = datetime.utcnow()
        if self.transit_days == "None":
            self.transit_days = -1

        self.clean_fields()

        RateSheet.objects.filter(
            carrier=self.carrier,
            origin_city=self.origin_city,
            origin_province=self.origin_province,
            destination_city=self.destination_city,
            destination_province=self.destination_province,
            service_code=self.service_code
        ).delete()

        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< RateSheet ({self.carrier.code}: {self.origin_city}, {self.origin_province.code}, " \
            f"{self.origin_province.country.code} to {self.destination_city}, {self.destination_province.code}, " \
            f"{self.destination_province.country.code} ({self.id})) >"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier.name}: {self.origin_city}, {self.origin_province.code}, " \
            f"{self.origin_province.country.code} to {self.destination_city}, {self.destination_province.code}, " \
            f"{self.destination_province.country.code}"
