"""
    Title: Address Validators
    Description: This file will contain functions for address validating.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import re

from rest_framework import serializers

from api.globals.project import POSTAL_CODE_REGEX
from api.models import Province


class PostalCodeValidator:

    def __init__(self, postal_code: str, province: str, country: str):
        self.postal_code = postal_code
        self.province = province
        self.country = country

    def valid(self) -> str:
        postal_code = self.postal_code.strip().upper()

        regex = POSTAL_CODE_REGEX.get(self.country, "^.*$")

        if not re.fullmatch(regex, postal_code):
            postal_code_format = {
                "CA": "A9A9A9",
                "US": "99999"
            }
            message = f'This field does not match {self.country} format of {postal_code_format.get(self.country, "")}.'
            raise serializers.ValidationError({'postal_code': [message]})

        return postal_code


class ProvinceValidator:

    def __init__(self, province: str, country: str):
        self.province = province
        self.country = country

    def valid(self) -> tuple:
        province = self.province.strip().upper()
        country = self.country.strip().upper()

        if not Province.objects.filter(code=province, country__code=country).exists():
            message = f"The combination of 'province': '{province}' and 'country': '{country}' are invalid."
            raise serializers.ValidationError({'province': [message]})

        return province, country
