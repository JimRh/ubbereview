"""
    Title: CarrierMarkup Model
    Description: This file will contain functions for CarrierMarkup Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields import DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import PERCENTAGE_PRECISION, MAX_PERCENTAGE_DIGITS
from api.models import Markup, Carrier
from api.models.base_table import BaseTable


class CarrierMarkup(BaseTable):
    """
        Carrier Markup Model
    """

    markup = ForeignKey(Markup, on_delete=CASCADE, related_name='carrier_markup_markup')
    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name='carrier_markup_carrier')
    percentage = DecimalField(decimal_places=PERCENTAGE_PRECISION, max_digits=MAX_PERCENTAGE_DIGITS)

    class Meta:
        verbose_name = "Carrier Markup"
        verbose_name_plural = "Carrier - Carrier Markup"
        ordering = ["markup", "carrier"]
        unique_together = ("markup", "carrier")

    @classmethod
    def create(cls, param_dict: dict = None) -> 'CarrierMarkup':
        """
            Create Carrier Markup
            :param param_dict: Carrier Markup Fields, described above
            :return: Carrier Markup Object
        """
        carrier_markup = cls()
        if param_dict is not None:
            carrier_markup.set_values(param_dict)
            carrier_markup.markup = param_dict.get("markup")
            carrier_markup.carrier = param_dict.get("carrier")
        return carrier_markup

    # Override
    def __repr__(self) -> str:
        return f"{self.carrier.name}, {self.markup.name}: {str(self.percentage)}%"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier.name}, {self.markup.name}: {str(self.percentage)}%"
