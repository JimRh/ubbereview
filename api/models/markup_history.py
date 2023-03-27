"""
    Title: Markup History Model
    Description: This file will contain functions for Markup History Model.
    Created: October 27, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models import ForeignKey, CASCADE, DateTimeField
from django.db.models.fields import CharField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Markup
from api.models.base_table import BaseTable


class MarkupHistory(BaseTable):
    """
        Markup History Model
    """

    markup = ForeignKey(Markup, on_delete=CASCADE, related_name='history_markup')
    change_date = DateTimeField(auto_now_add=True, help_text="Date of markup change.")
    username = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Individual who updated the markup.")
    old_value = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Old value.")
    new_value = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Updated value")

    class Meta:
        verbose_name = "Markup History"
        ordering = ["markup", "change_date"]

    # Override
    def __repr__(self) -> str:
        return f"< MarkupHistory ({str(self.markup)}, {self.username}, {self.old_value}, {self.new_value})"

    # Override
    def __str__(self) -> str:
        return f"{str(self.markup)}: {self.username}, {self.old_value} to {self.new_value}"
