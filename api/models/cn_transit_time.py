"""
    Title: TransitTime Model
    Description: This file will contain functions for TransitTime Model for canadian north transit times.
    Created: July 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import CharField, PositiveIntegerField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models.base_table import BaseTable


class TransitTime(BaseTable):
    """
        TransitTime Model
    """

    origin = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Airport code for origin.")
    destination = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Airport code for destination.")
    rate_priority_id = PositiveIntegerField(help_text="Rate priority identifier of the NOG")
    rate_priority_code = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Service Name")
    transit_min = PositiveIntegerField(help_text="Min Transit time for service")
    transit_max = PositiveIntegerField(help_text="Max Transit time for service")

    class Meta:
        verbose_name = "Transit Time"
        verbose_name_plural = "CN - Transit Time's"

    # Override
    def __repr__(self) -> str:
        return f"< TransitTime ({self.origin}, {self.destination}, {self.rate_priority_id}, {self.rate_priority_code}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.origin} to {self.destination}, {self.rate_priority_code}, {self.transit_min}-{self.transit_max}"
