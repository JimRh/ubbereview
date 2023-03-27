"""
    Title: CarrierOption Model
    Description: This file will contain functions for CarrierOption Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ValidationError
from django.db.models.deletion import CASCADE
from django.db.models.fields.related import ForeignKey

from api.models import OptionName, Carrier
from api.models.option import Option


class CarrierOption(Option):
    """
        CarrierOption Model
    """

    option = ForeignKey(OptionName, on_delete=CASCADE, related_name="carrier_option_option")
    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name="carrier_option_carrier")

    class Meta:
        verbose_name = "Carrier Option"
        verbose_name_plural = "Option - Carrier Options"
        ordering = ["option__name", "carrier__name"]
        unique_together = ("option", "carrier")

    # Override
    def clean(self) -> None:
        if self.option.is_mandatory:
            raise ValidationError("Carrier option cannot be a mandatory option")

    # Override
    def save(self, *args, **kwargs) -> None:
        self.minimum_value = self.minimum_value.quantize(self._price_sig_fig)
        self.maximum_value = self.maximum_value.quantize(self._price_sig_fig)
        self.percentage = self.percentage.quantize(self._percentage_sig_fig)

        self.clean_fields()
        self.clean()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< CarrierOption ({self.option}: {repr(self.carrier)}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.option}: {self.carrier}"
