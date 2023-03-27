"""
    Title: Country Model
    Description: This file will contain functions for Province Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re

from django.db.models.fields import CharField

from api.globals.project import DEFAULT_CHAR_LEN, COUNTRY_CODE_LEN, CURRENCY_CODE_LEN, MAX_CHAR_LEN, STRICT_STRING_REGEX
from api.models.base_table import BaseTable


class Country(BaseTable):
    name = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    code = CharField(max_length=COUNTRY_CODE_LEN, unique=True,help_text="The ISO_3166_1 letter code of the country")
    currency_name = CharField(max_length=DEFAULT_CHAR_LEN)
    currency_code = CharField(max_length=CURRENCY_CODE_LEN, help_text="ISO 4217 letter code of the currency")
    _iata_name = CharField(max_length=MAX_CHAR_LEN, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.name = self.name.title()
        self.code = re.sub(STRICT_STRING_REGEX, '', self.code).upper()
        self.currency_code = re.sub(STRICT_STRING_REGEX, '', self.currency_code).upper()

        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Country ({self.name}: {self.code}) >"

    # Override
    def __str__(self) -> str:
        return self.name
