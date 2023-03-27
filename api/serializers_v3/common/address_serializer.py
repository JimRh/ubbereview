"""
    Title: Country  Serializers
    Description: This file will contain all functions for country serializers.
    Created: December 18, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import DEFAULT_CHAR_LEN, COUNTRY_CODE_LEN, PROVINCE_CODE_LEN
from api.models import Address


class AddressSerializer(serializers.ModelSerializer):

    address_two = serializers.CharField(
        help_text='Address Two',
        max_length=DEFAULT_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    province = serializers.CharField(
        source="province.code",
        max_length=PROVINCE_CODE_LEN,
        help_text='Province code. Ex: AB.'
    )

    country = serializers.CharField(
        source="province.country.code",
        max_length=COUNTRY_CODE_LEN,
        help_text='Province code. Ex: CA.'
    )

    has_shipping_bays = serializers.BooleanField(
        help_text='Is the address residential?',
        required=True,
    )

    class Meta:
        model = Address
        fields = [
            'id',
            'address',
            'address_two',
            'city',
            'province',
            'country',
            'postal_code',
            'has_shipping_bays'
        ]
