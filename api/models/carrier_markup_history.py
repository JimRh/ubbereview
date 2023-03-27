"""
    Title: Carrier Markup History Model
    Description: This file will contain functions for Carrier Markup History Model.
    Created: October 27, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models import ForeignKey, CASCADE, DateTimeField
from django.db.models.fields import CharField

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import CarrierMarkup
from api.models.base_table import BaseTable


class CarrierMarkupHistory(BaseTable):
    """
        Carrier Markup History Model
    """

    carrier_markup = ForeignKey(CarrierMarkup, on_delete=CASCADE, related_name='history_carrier_markup')
    change_date = DateTimeField(auto_now_add=True, help_text="Date of carrier markup change.")
    username = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Individual who updated the carrier markup.")
    old_value = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Old value.")
    new_value = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Updated value")

    class Meta:
        verbose_name = "Carrier Markup History"
        ordering = ["carrier_markup", "change_date"]

    @property
    def carrier(self):
        return self.carrier_markup.carrier.name

    @property
    def markup(self):
        return self.carrier_markup.markup.name

    # Override
    def __repr__(self) -> str:
        return f"< CarrierMarkupHistory ({str(self.carrier_markup)}, {self.username}, {self.old_value}, {self.new_value})"

    # Override
    def __str__(self) -> str:
        return f"{str(self.carrier_markup)}, {self.username}, {self.old_value} to {self.new_value}"
