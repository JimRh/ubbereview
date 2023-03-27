"""
    Title: SealiftSailingDates Model
    Description: This file will contain functions for SealiftSailingDates Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from datetime import timedelta, datetime

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, DateTimeField, DecimalField
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.utils import timezone

from api.globals.project import LETTER_MAPPING_LEN, WEIGHT_PRECISION, MAX_WEIGHT_DIGITS
from api.models import Carrier, Port
from api.models.base_table import BaseTable


class SealiftSailingDates(BaseTable):
    """
        SealiftSailingDates Model
    """

    _SAILING_NAME = (
        ("FI", "First Sailing"),
        ("SE", "Second Sailing"),
        ("TH", "Third Sailing")
    )

    _status = (
        ("EP", "Empty"),
        ("OT", "One Third Full"),
        ("HF", "Half Full"),
        ("TF", "Three Quarters Full"),
        ("FU", "Full")
    )

    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name="sealift_carrier")
    port = ForeignKey(Port, on_delete=CASCADE, related_name="sealift_port")
    port_destinations = ManyToManyField(Port, related_name='sailing_date_ports')
    name = CharField(max_length=LETTER_MAPPING_LEN*2, choices=_SAILING_NAME, help_text="Sailing Type")
    sailing_date = DateTimeField(
        help_text="Sailing Date of the carrier",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    dg_packing_cutoff = DateTimeField(
        help_text="Dangerous Goods packaging cut off date",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    cargo_packing_cutoff = DateTimeField(
        help_text="Cargo packaging cut off date",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    bbe_dg_cutoff = DateTimeField(
        help_text="BBE Dangerous Goods packaging cut off date",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )

    bbe_cargo_cutoff = DateTimeField(
        help_text="BBE Cargo packaging cut off date",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    weight_capacity = DecimalField(
        decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS, help_text="Weight Capacity of the sailing"
    )
    current_weight = DecimalField(
        decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS, help_text="Current Weight of the sailing"
    )
    status = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_status, default="EP", help_text="Status of Sailing")

    class Meta:
        verbose_name = "Sealift Sailing Date"
        verbose_name_plural = "Sealift Sailing Dates"
        ordering = ["carrier", "name"]

    @classmethod
    def create(cls, param_dict: dict = None) -> 'SealiftSailingDates':
        """
            Create Sailing Date
            :param param_dict: Sailing Date Fields, described above
            :return: Carrier Sailing Date Object
        """
        sailing_date = cls()
        if param_dict is not None:
            sailing_date.set_values(param_dict)
            sailing_date.carrier = param_dict.get("carrier")
            sailing_date.port = param_dict.get("port")
        return sailing_date

    # Override
    def save(self, *args, **kwargs) -> None:
        one_week = timedelta(days=7)
        self.bbe_cargo_cutoff = self.cargo_packing_cutoff - one_week
        self.bbe_dg_cutoff = self.dg_packing_cutoff - one_week

        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< SealiftSailingDates ({self.carrier} - {self.name} - {self.sailing_date.strftime('%Y-%m-%d')}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier} - {self.name} - {self.sailing_date.strftime('%Y-%m-%d')}"
