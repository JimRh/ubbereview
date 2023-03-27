"""
    Title: Exchange Rate Model
    Description: This file will contain functions for Exchange Rate Model and is mainly a lookup table.
    Created: September 29, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.db.models import CharField
from django.db.models.fields import DateTimeField, DecimalField
from pytz import UTC

from api.globals.project import CURRENCY_CODE_LEN, EXCHANGE_RATE_PRECISION, MAX_PRICE_DIGITS
from api.models.base_table import BaseTable


class ExchangeRate(BaseTable):
    """
        Exchange Rate Database Table
    """
    # Hours
    _expire_time = 24

    exchange_rate_date = DateTimeField(auto_now_add=True, help_text="Date of exchange rate")
    expire_date = DateTimeField(null=True, blank=True, help_text="Exchange rate expire date.")
    source_currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Currency Code to start from.")
    target_currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Currency Code to end in.")
    exchange_rate = DecimalField(
        decimal_places=EXCHANGE_RATE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="Exchange rate to be used to go from source to target currency.",
    )

    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rate's"
        unique_together = ("source_currency", "target_currency")

    # Override
    def save(self, *args, **kwargs) -> None:
        self.expire_date = datetime.datetime.now(tz=UTC) + datetime.timedelta(hours=self._expire_time)
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< ExchangeRate ({self.source_currency}, {self.target_currency}, {self.exchange_rate})) >"

    # Override
    def __str__(self) -> str:
        return f"{self.source_currency}, {self.target_currency}, {self.exchange_rate}"
