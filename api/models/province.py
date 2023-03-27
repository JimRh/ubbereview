"""
    Title: Province Model
    Description: This file will contain functions for Province Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN, PROVINCE_CODE_LEN, STRICT_STRING_REGEX
from api.models import Country
from api.models.base_table import BaseTable


class Province(BaseTable):
    name = CharField(max_length=DEFAULT_CHAR_LEN)
    code = CharField(max_length=PROVINCE_CODE_LEN, help_text="The ISO_3166_1 letter code of the country province")
    country = ForeignKey(Country, on_delete=CASCADE, related_name='province_country')

    class Meta:
        ordering = ["name"]

    @staticmethod
    def get_province(code: str, country: str) -> 'Province':
        """
            Function will return a province object if it exists for the combination of province code and country.
            :param code: Province Code
            :param country: Country Code
            :return: Province
        """

        try:
            record = Province.objects.get(code=code, country__code=country)
        except ObjectDoesNotExist:
            raise Exception(f"No province found for {code} and country {country}")

        return record

    # Override
    def save(self, *args, **kwargs) -> None:
        self.name = self.name.title()
        self.code = re.sub(STRICT_STRING_REGEX, '', self.code).upper()
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Province ({self.name}: {self.code}, {self.country.name}: {self.country.code}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.name}, {self.country.name}"
