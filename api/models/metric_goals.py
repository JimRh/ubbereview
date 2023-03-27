"""
    Title: Daily Metric Goal Model
    Description: This file will contain views that only relate to Metric Goal Model.
    Created: Jan 3, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db.models.fields import CharField, DateTimeField, DecimalField
from django.utils.timezone import now

from api.globals.project import PRICE_PRECISION, MAX_PRICE_DIGITS, BASE_TEN, PERCENTAGE_PRECISION, \
    DEFAULT_CHAR_LEN, LETTER_MAPPING_LEN
from api.models.base_table import BaseTable


class MetricGoals(BaseTable):

    # Future move to DB?
    _SYSTEM = (
        ("BE", "BBE"),
        ("UB", "ubbe"),
        ("FE", "Fetchable"),
        ("DE", "DeliverEase"),
        ("TP", "Third Party"),  # Public Api Clients or just set them to ubbe?
    )

    SYSTEM_LIST = [
        "BE",
        "UB",
        "FE",
        "DE",
        "TP"
    ]

    _cost_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _percentage_sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))

    system = CharField(
        max_length=LETTER_MAPPING_LEN * 2, choices=_SYSTEM, default="UB", help_text="System Metrics Belong to."
    )
    start_date = DateTimeField(default=now, help_text="Metric Start date")
    end_date = DateTimeField(help_text="Metric End date")
    name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Goal name.")
    current = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Current goal position."
    )
    goal = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Goal End point.")
    icon = CharField(default="", max_length=DEFAULT_CHAR_LEN, help_text="Icon Name.", blank=True, null=True)

    class Meta:
        verbose_name = 'Metric Goal'
        verbose_name_plural = 'Metric Goals'
        ordering = ["system", "start_date", "end_date"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.current = self.current.quantize(self._cost_sig_fig)
        self.goal = self.goal.quantize(self._percentage_sig_fig)

        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< MetricGoals ({self.system}: {self.start_date} - {self.end_date}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.system}: {self.start_date} - {self.end_date}"
