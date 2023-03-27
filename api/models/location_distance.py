"""
    Title: Location Distance Model
    Description: This file will contain functions for Location Distance Model.
    Created: March 1, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models import PROTECT, ForeignKey
from django.db.models.fields import CharField, DecimalField

from api.globals.project import DEFAULT_CHAR_LEN, DIMENSION_PRECISION, MAX_DIMENSION_DIGITS
from api.models import Province
from api.models.base_table import BaseTable


class LocationDistance(BaseTable):
    """
        Location Distance Model
    """

    origin_city = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Origin City")
    origin_province = ForeignKey(
        Province, on_delete=PROTECT, related_name='ld_origin_province', help_text="Origin Province"
    )
    destination_city = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Destination City")
    destination_province = ForeignKey(
        Province, on_delete=PROTECT, related_name='ld_destination_province', help_text="Destination Province"
    )
    distance = DecimalField(
        decimal_places=DIMENSION_PRECISION, max_digits=MAX_DIMENSION_DIGITS, help_text="Distance between locations.(km)"
    )
    duration = DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text="Duration between locations.(Seconds)"
    )

    class Meta:
        verbose_name = "Location Distance"
        verbose_name_plural = "Location Distances"
        unique_together = ("origin_city", "origin_province", "destination_city", "destination_province")
        ordering = (
            'origin_city',
            'origin_province',
            'destination_city',
            'destination_province',
            'distance',
            'duration'
        )

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
            obj.origin_province = param_dict.get('origin_province')
            obj.destination_province = param_dict.get('destination_province')
        return obj

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< LocationDistance ({self.origin_city}, {self.origin_province.code}, {self.destination_city}, " \
            f"{self.destination_province.code}, {self.distance}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.origin_city}, {self.origin_province.code}, {self.destination_city}, " \
            f"{self.destination_province.code}, {self.distance}"
