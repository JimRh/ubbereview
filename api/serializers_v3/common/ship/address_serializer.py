"""
    Title: Ship Address Serializers
    Description: This file will contain all functions for ship address serializers.
    Created: March 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import API_CHAR_LEN, POSTAL_CODE_LEN, API_PROVINCE_CODE_LEN, API_COUNTRY_CODE_LEN, \
    API_PHONE_MIN, API_PHONE_MAX, API_CHAR_MID_LEN, API_MAX_PROVINCE_CODE_LEN
from api.serializers_v3.validators.address_validators import PostalCodeValidator, ProvinceValidator
from api.serializers_v3.validators.contact_validators import PhoneValidator


class ShipAddressSerializer(serializers.Serializer):

    address = serializers.CharField(
        help_text='Proper Address',
        max_length=API_CHAR_LEN,
    )

    address_two = serializers.CharField(
        help_text='Additional Address Information',
        max_length=API_CHAR_LEN,
        required=False
    )

    city = serializers.CharField(
        help_text='Proper City Name',
        max_length=API_CHAR_LEN,
    )

    province = serializers.CharField(
        max_length=API_MAX_PROVINCE_CODE_LEN,
        min_length=API_PROVINCE_CODE_LEN,
        help_text='Province code. Ex: AB.'
    )

    country = serializers.CharField(
        max_length=API_COUNTRY_CODE_LEN,
        min_length=API_COUNTRY_CODE_LEN,
        help_text='Country code. Ex: CA.'
    )

    postal_code = serializers.CharField(
        help_text='Proper Postal Code',
        max_length=POSTAL_CODE_LEN,
    )

    # TODO: Replace has_shipping_bays to is_residential (Proper Term)
    has_shipping_bays = serializers.BooleanField(
        help_text='Is the address not residential?',
    )

    # Contact Fields
    company_name = serializers.CharField(
        help_text='Company name',
        max_length=API_CHAR_LEN,
        required=False
    )

    name = serializers.CharField(
        help_text='Contact name',
        max_length=API_CHAR_LEN
    )

    phone = serializers.CharField(
        help_text='Phone number',
        min_length=API_PHONE_MIN,
        max_length=API_PHONE_MAX,
    )

    email = serializers.EmailField(
        max_length=API_CHAR_MID_LEN,
        help_text='Email address'
    )

    def validate(self, data):
        data["city"] = data["city"].strip().title()

        # Validate Province to country.
        data["province"], data["country"] = ProvinceValidator(
            province=data["province"], country=data["country"]
        ).valid()

        # Validate Postal Code to the country.
        data["postal_code"] = PostalCodeValidator(
            postal_code=data["postal_code"], province=data["province"], country=data["country"]
        ).valid()

        data["name"] = data["name"].strip().title()
        data["company_name"] = data.get("company_name", data["name"]).strip().title()

        # Validate Phone
        data["phone"] = PhoneValidator(phone=data["phone"]).valid()

        return data
