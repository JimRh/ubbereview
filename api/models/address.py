"""
    Title: Address Model
    Description: This file will contain functions for Address Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, BooleanField
from django.db.models.fields.related import ForeignKey

from api.exceptions.project import DatabaseException
from api.globals.project import DEFAULT_CHAR_LEN, MAX_CHAR_LEN, POSTAL_CODE_LEN, DEFAULT_STRING_REGEX, POSTAL_CODE_REGEX
from api.models import Province
from api.models.base_table import BaseTable
from apps.common.utilities.address import clean_address, clean_postal_code, clean_city


class Address(BaseTable):
    """
        Address Model
    """

    province = ForeignKey(Province, on_delete=PROTECT, related_name='address_province')
    city = CharField(max_length=DEFAULT_CHAR_LEN)
    address = CharField(max_length=MAX_CHAR_LEN)
    address_two = CharField(max_length=MAX_CHAR_LEN, blank=True)
    postal_code = CharField(max_length=POSTAL_CODE_LEN)
    has_shipping_bays = BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["province", "city"]

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create Address from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Address Object
        """

        address = cls()
        if param_dict is not None:
            address.set_values(param_dict)
            address.province = param_dict.get("province")
        return address

    @classmethod
    def create_or_find(cls, param_dict: dict):
        """
            Create or Find Address from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Address Object
        """

        lookup_dict = {}
        province_code = param_dict.get("province", '')
        country_code = param_dict.get("country", '')

        try:
            province = Province.objects.get(code=province_code, country__code=country_code)
        except ObjectDoesNotExist:
            raise DatabaseException(
                {
                    f'api.error": "Province: \'{province_code}\' and country: \'{country_code}\' does not exist.'
                }
            )

        lookup_dict["city"] = clean_city(param_dict.get("city", ''))
        lookup_dict["address"] = clean_address(param_dict.get("address", ''))
        lookup_dict["postal_code"] = clean_postal_code(param_dict.get("postal_code", ''))
        lookup_dict['province'] = province
        lookup_dict['country'] = province.country

        address = Address.find(lookup_dict)

        if address is None:
            address = cls.create(lookup_dict)
            address.save()

        return address

    @staticmethod
    def find(param_dict: dict):
        """
            Find Address from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Address Object
        """

        country_obj = param_dict.get("country")

        if country_obj is None:
            raise DatabaseException({"api.error": "Country object not found"})

        province_obj = param_dict.get("province")

        if province_obj is None:
            raise DatabaseException({"api.error": "Province object not found"})

        address = Address.objects.filter(
            city=param_dict.get("city", ''),
            address=param_dict.get("address", ''),
            postal_code=param_dict.get("postal_code", ''),
            province__country=country_obj,
            province=province_obj
        ).first()

        return address

    @property
    def get_ship_dict(self) -> dict:
        """
            Get Address details for next leg shipping.
            :return: Address and Contact dict
        """

        return {
            "address": self.address,
            "city": self.city,
            "province": self.province.code,
            "country": self.province.country.code,
            "postal_code": self.postal_code
        }

    def next_leg_json(self, contact) -> dict:
        """
            Get Address details for next leg shipping.
            :param contact: Contact
            :return: Address and Contact dict
        """

        next_leg_json = {
            "address": self.address,
            "city": self.city,
            "country": self.province.country.code,
            "postal_code": self.postal_code,
            "province": self.province.code
        }

        next_leg_json.update(contact.next_leg_json())

        return next_leg_json

    # Override
    def clean(self) -> None:
        regex = POSTAL_CODE_REGEX.get(self.province.country.code, "^.*$")

        if not re.fullmatch(regex, self.postal_code):
            postal_code_format = {
                "CA": "A9A9A9",
                "US": "99999"
            }
            raise ValidationError(
                f"Postal code for {self.province.country.name} does not match format "
                f"{postal_code_format[self.province.country.code]}"
            )

    # Override
    def save(self, *args, **kwargs) -> None:
        self.city = clean_city(self.city)
        self.address = clean_address(address=self.address)
        self.postal_code = clean_postal_code(self.postal_code)
        self.clean_fields()
        self.clean()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Address ({self.address}, {self.city}, {repr(self.province)}, {self.postal_code}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.address}, {self.city}, {self.province}, {self.postal_code}"
