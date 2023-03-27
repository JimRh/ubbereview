"""
    Title: CityNameAlias Model
    Description: This file will contain functions for CityNameAlias Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Province, Carrier
from api.models.base_table import BaseTable


class CityNameAlias(BaseTable):
    """
        CityNameAlias Model
    """

    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name="city_name_alias_carrier")
    province = ForeignKey(Province, on_delete=CASCADE, related_name="city_name_alias_province")
    name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The city proper name")
    alias = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The non standard name for the associated city")

    class Meta:
        verbose_name = "City Name Alias"
        verbose_name_plural = "Carrier - City Name Aliases"
        ordering = ["carrier", "name"]

    @staticmethod
    def check_alias(alias: str, province_code: str, country_code: str, carrier_id: int) -> str:
        """
            Check for BBE City Alias for Stats and Business Central Pushing
            :param carrier_id: Carrier ID
            :param alias: str - City Alias to check
            :param province_code: str - Province Code
            :param country_code: str - Country Code
            :return: City or City Alias Found
        """

        try:
            return CityNameAlias.objects.get(
                alias=alias,
                province__code=province_code,
                province__country__code=country_code,
                carrier__code=carrier_id,
            ).name
        except ObjectDoesNotExist:
            return alias

    # Override
    def clean(self) -> None:
        if self.name.lower() == self.alias.lower():
            raise ValidationError("Name and Alias cannot be the same")

    # Override
    def save(self, *args, **kwargs):
        self.clean_fields()
        self.clean()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< CityAlias ({self.carrier.name}: {self.name}, {self.alias}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.carrier.name}: {self.name}, {self.alias}"
