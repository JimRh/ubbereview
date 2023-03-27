"""
    Title: Canadian North Interline Model
    Description: This file will contain functions for Interline Model for canadian north interline lanes.
    Created: Jan 12, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.fields import CharField, IntegerField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models.base_table import BaseTable


class CNInterline(BaseTable):
    """
        CN Interline Model
    """

    origin = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Airport code for origin.")
    destination = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Airport code for destination.")
    interline_id = IntegerField(help_text="Interline group id provide by skyline.")
    interline_carrier = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Interline carrier name.")

    class Meta:
        verbose_name = "CN Interline"
        verbose_name_plural = "CN - Interline's"

    # Override
    def __repr__(self) -> str:
        return f"< CNInterline ({self.origin}, {self.destination}, {self.interline_id}, {self.interline_carrier}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.origin} to {self.destination}, {self.interline_id}, {self.interline_carrier}"
