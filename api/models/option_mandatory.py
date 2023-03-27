"""
    Title: Address Model
    Description: This file will contain functions for Address Model.
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


class MandatoryOption(Option):
    """
        Address Model
    """

    option = ForeignKey(OptionName, on_delete=CASCADE, related_name="mandatory_option_option")
    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name="mandatory_option_carrier")

    class Meta:
        verbose_name = "Mandatory Option"
        verbose_name_plural = "Option - Mandatory Options"
        ordering = ["option__name", "carrier__name"]
        unique_together = ["option", "carrier"]

    # Override
    def clean(self) -> None:
        if not self.option.is_mandatory:
            raise ValidationError("Carrier option must be a mandatory option")

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
        return f"< MandatoryOption ({self.option}: {self.carrier}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.option}: {self.carrier}"
