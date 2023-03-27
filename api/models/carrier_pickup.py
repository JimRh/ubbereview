"""
    Title: Carrier Pickup Model
    Description: This file will contain functions for carrier pickup and its limitations.
    Created: August 15, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, IntegerField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Carrier
from api.models.base_table import BaseTable


class CarrierPickupRestriction(BaseTable):
    """
        Carrier Pickup Restriction Model
    """

    carrier = ForeignKey(
        Carrier, on_delete=PROTECT, related_name="carrier_pickup_carrier", help_text="Carrier Pickup Restrictions"
    )
    # service = CharField(
    #     max_length=DEFAULT_CHAR_LEN, help_text="Carrier Service for pickup restrictions and information.?"
    # )
    min_start_time = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Min start time for pickup. Ex: 08:00. Used for dropdown min time."
    )
    max_start_time = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Max start time for pickup. Ex: 10:00."
    )
    min_end_time = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Min End time for pickup. Ex: 14:00."
    )
    max_end_time = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Max End time for pickup. Ex: 16:00. Used for dropdown max time."
    )
    pickup_window = IntegerField(
        help_text="Min amount of window for time. (In Hours) EX: 2"
    )
    min_time_same_day = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Minimum time for same day pickup for the carrier."
    )
    max_pickup_days = IntegerField(
        help_text="Max date to book pickups for the future. (Enter Days - Whole Number)"
    )

    class Meta:
        verbose_name = "Carrier Pickup Restrictions"
        verbose_name_plural = "Carrier - Carrier Pickup Restrictions"
        ordering = ["carrier__name"]

    @staticmethod
    def default_pickup_restrictions() -> dict:
        return {
            "id": -1,
            "carrier_name": "default",
            "carrier_id": -1,
            "min_start_time": "07:00",
            "max_start_time": "16:00",
            "min_end_time": "09:00",
            "max_end_time": "18:00",
            "pickup_window": 2,
            "min_time_same_day": "14:00",
            "max_pickup_days": 14
        }

    # Override
    def __repr__(self) -> str:
        return f"< CarrierPickupRestriction ({self.carrier.name}, {self.min_start_time}, {self.max_end_time}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier.name}, {self.min_start_time}, {self.max_end_time}, {self.min_time_same_day}"
