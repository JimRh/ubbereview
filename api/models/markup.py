"""
    Title: Markup Model
    Description: This file will contain functions for Markup Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import CharField, DecimalField, BooleanField

from api.background_tasks.logger import CeleryLogger
from api.globals.project import DEFAULT_CHAR_LEN, PERCENTAGE_PRECISION, MAX_PERCENTAGE_DIGITS, BASE_TEN, \
    DEFAULT_STRING_REGEX
from api.models import Carrier
from api.models.base_table import BaseTable


class Markup(BaseTable):
    """
        Markup Model
    """

    _sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))
    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True, help_text="Name of Markup")
    default_percentage = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="Whole Number of markup percentage: Ex: 15 for 15%"
    )
    default_carrier_percentage = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="Only used to default new carries to carrier markup, Whole Number of markup percentage: Ex: "
                  "15 for 15%",
        default=Decimal("0"),
        null=True,
        blank=True
    )
    description = CharField(max_length=DEFAULT_CHAR_LEN, blank=True, help_text="Description of Markup")
    is_template = BooleanField(default=False, help_text="Is the markup a template markup?")

    class Meta:
        verbose_name = "Markup"
        ordering = ["name"]

    def markup_multiplier(self, carrier_id: int) -> Decimal:
        """
            Returns the Markup Multiplier for a Shipment. ((Account Markup/100) + (Carrier Markup/100)) + 1
            :param carrier_id: Carrier ID: Ex: FedEx: 2
            :return: Decimal Value
        """

        try:
            carrier_markup = self.carrier_markup_markup.get(carrier__code=carrier_id)
        except ObjectDoesNotExist as e:
            CeleryLogger().l_error.delay(
                location="models.py line: 523",
                message="Markup {}: Carrier Markup does not exist for {}".format(self.name, carrier_id)
            )
            return (self.default_percentage / self._hundred) + self._one

        return (self.default_percentage / self._hundred) + (carrier_markup.percentage / self._hundred) + self._one

    def get_carrier_percentage(self, carrier: Carrier) -> Decimal:
        """
            Returns the carrier markup
            :param carrier: Carrier Object
            :return: Decimal Value
        """
        try:
            carrier_markup = self.carrier_markup_markup.get(carrier=carrier)
        except ObjectDoesNotExist as e:
            CeleryLogger().l_error.delay(
                location="models.py line: 523",
                message="Markup {}: Carrier Markup does not exist for {}".format(self.name, carrier)
            )
            return self.default_percentage
        return carrier_markup.percentage

    # Override
    def clean(self) -> None:
        self.name = re.sub(DEFAULT_STRING_REGEX, '', self.name).title()

    # Override
    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"{self.name}: {str(self.default_percentage)}%"

    # Override
    def __str__(self) -> str:
        return f"{self.name}: {str(self.default_percentage)}%"
