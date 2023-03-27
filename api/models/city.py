"""
    Title: City Model
    Description: This file will contain functions for City Model.
                 City names is used but can include Towns, Villages, etc..
    Created: August 20, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

# TODO - Move Airport DB to this model
# TODO - Move Port DB to this model
# TODO - Move BBE City alias DB to this model
from typing import Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, IntegerField, BooleanField, TextField
from django.db.models.fields.related import ForeignKey

from api.apis.google.place_apis.timezone_api import GoogleTimezoneApi
from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_CHAR_LEN, ISO_3166_1_LEN, MAX_TEXT_LEN
from api.models import Province, Address
from api.models.base_table import BaseTable


class City(BaseTable):
    """
        City Model
    """

    name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The city proper name")
    aliases = TextField(
        max_length=MAX_TEXT_LEN,
        help_text="Alias for the city. Separated by Comma.",
        default="",
        blank=True
    )
    province = ForeignKey(Province, on_delete=CASCADE, related_name="city_province")
    google_place_id = CharField(
        max_length=DEFAULT_CHAR_LEN,
        help_text="is a unique identifier that can be used with other Google APIs. For example, you can use the "
                  "place_id in a Places API request to get details of a local business, such as phone number, "
                  "opening hours, user reviews, and more.",
        blank=True,
        default=""
    )
    timezone = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The city proper name", default="", blank=True)
    timezone_name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The city proper name", default="", blank=True)
    timezone_dst_off_set = IntegerField(
        default=0,
        help_text="The offset for daylight-savings time in seconds. "
                  "This will be zero if the time zone is not in Daylight Savings Time during the specified timestamp.",
        blank=True
    )
    timezone_raw_off_set = IntegerField(
        default=0,
        help_text="The offset from UTC (in seconds) for the given location. "
                  "This does not take into effect daylight savings.",
        blank=True
    )
    latitude = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Latitude for city location", default="", blank=True)
    longitude = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Longitude for city location", default="", blank=True)
    airport_code = CharField(max_length=ISO_3166_1_LEN, help_text="IATA Airport Code", default="", blank=True)
    airport_name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="IATA Airport Name", default="", blank=True)
    airport_address = ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete=CASCADE,
        related_name='city_airport_address',
        help_text="Main address for airport."
    )
    has_airport = BooleanField(default=False, help_text="Does the city have an airport? (The main airport if two.)")
    has_port = BooleanField(default=False, help_text="Does the city have an port? (The main port if two.)")

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "City's"
        ordering = ["name", "province"]
        unique_together = ["name", "province"]

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create City from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: City Object
        """

        record = cls()
        if param_dict is not None:
            record.set_values(param_dict)
            record.province = param_dict.get("province")
            record.airport_address = param_dict.get("airport_address")

        return record

    @staticmethod
    def get_city(name: str, province: str, country: str) -> Union['City', None]:
        """
            Get city for params name, province, and country.
            :param name: City Name
            :param province: Province Code
            :param country: Country Code
            :return: city object or none
        """

        try:
            city = City.objects.filter(
                aliases__icontains=name.lower(), province__code=province, province__country__code=country
            ).first()
        except ObjectDoesNotExist:
            city = None

        return city

    def get_timezone(self, name: str, province: str, country: str, is_object: bool = False) -> str:
        """
            Get timezone for name, province, and country. If doesn't exist create new city and get timezone information.
            :return:
        """

        city = self.get_city(name=name.lower(), province=province, country=country)

        if city and city.timezone:
            return city if is_object else city.timezone

        try:
            data = GoogleTimezoneApi().get_timezone(city=name, province=province, country=country)
        except ViewException as e:
            raise ViewException(code=e.code, message=e.message, errors=e.errors)

        # Try and get city after getting locality from google geo, should help with alias somewhat
        city = self.get_city(name=data["long_name"], province=province, country=country)

        # Still not found, create new one.
        if not city:
            province = Province.get_province(code=province, country=country)
            params = {"name": data["long_name"], "province": province}
            city = City.create(param_dict=params)

        # Otherwise update city with information.
        if name.lower() not in city.aliases.split(","):
            city.aliases += f"{name.lower()},"

        if data["long_name"] not in city.aliases.split(","):
            city.aliases += f'{data["long_name"]},'

        if data["short_name"] not in city.aliases.split(","):
            city.aliases += f'{data["short_name"]},'

        city.set_values(pairs=data)
        city.save()

        return city if is_object else city.timezone

    # Override
    def __repr__(self) -> str:
        return f"< City ({self.name}: {self.province}, {self.timezone}, Lat: {self.latitude}, Long: {self.longitude}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.name}: {self.province}, {self.timezone}, Lat: {self.latitude}, Long: {self.longitude}"
