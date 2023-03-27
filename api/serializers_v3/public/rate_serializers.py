"""
    Title: Rate Serializers
    Description: This file will contain all functions for rate serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import WEIGHT_PRECISION, DIMENSION_PRECISION, API_MAX_PACK_CHAR, MAX_DIMENSION_DIGITS, \
    MAX_WEIGHT_DIGITS, API_ZERO, API_PACKAGE_TYPES, COUNTRY_CODE_LEN, API_CHAR_LEN, POSTAL_CODE_LEN, \
    API_PROVINCE_CODE_LEN, API_MAX_PROVINCE_CODE_LEN
from api.serializers_v3.public.pickup_request_serializer import PickupRequestSerializer
from api.serializers_v3.validators.address_validators import PostalCodeValidator, ProvinceValidator


class RatePackageSerializer(serializers.Serializer):

    package_type = serializers.ChoiceField(
        choices=API_PACKAGE_TYPES,
        help_text="Type of package, box, skid..."
    )

    quantity = serializers.IntegerField(
        help_text='Number of packages',
    )

    description = serializers.CharField(
        help_text='Description of package (Be Precise)',
        max_length=API_MAX_PACK_CHAR,
        allow_blank=True
    )

    # Skid Fields
    freight_class = serializers.CharField(
        help_text='NNFC Freight Class',
        max_length=API_MAX_PACK_CHAR,
        default="70.00"
    )

    length = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text='Length of package (Individual piece)',
    )

    width = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text='Width of package (Individual piece)',

    )

    height = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        help_text='Height of package (Individual piece)',
    )

    weight = serializers.DecimalField(
        decimal_places=WEIGHT_PRECISION,
        max_digits=MAX_WEIGHT_DIGITS,
        help_text='Weight of package (Individual piece)',
    )

    # CN ONLY Fields
    nog_id = serializers.CharField(
        help_text='Canadian North NOG ',
        max_length=API_MAX_PACK_CHAR,
        default="",
        allow_blank=True,
        required=False
    )


class RateAddressSerializer(serializers.Serializer):

    company_name = serializers.CharField(
        help_text='Company Name',
        max_length=API_CHAR_LEN,
        default="BBE"
    )

    address = serializers.CharField(
        help_text='Proper Address',
        max_length=API_CHAR_LEN,
        default="1234 Quote Street"
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
        max_length=COUNTRY_CODE_LEN,
        help_text='Country code. Ex: CA.'
    )

    postal_code = serializers.CharField(
        help_text='Proper Postal Code',
        max_length=POSTAL_CODE_LEN,
    )

    has_shipping_bays = serializers.BooleanField(
        help_text='Is the address not residential?',
    )

    def validate(self, data):
        # Validate Province to country.
        data["province"], data["country"] = ProvinceValidator(
            province=data["province"], country=data["country"]
        ).valid()

        # Validate Postal Code to the country.
        data["postal_code"] = PostalCodeValidator(
            postal_code=data["postal_code"], province=data["province"], country=data["country"]
        ).valid()

        return data


class RateRequestSerializer(serializers.Serializer):

    rate_id = serializers.UUIDField(
        format='hex_verbose',
        required=False
    )

    carrier_id = serializers.ListField(
        child=serializers.IntegerField(min_value=API_ZERO),
        help_text='List of carrier ids to request rates from.',
        required=False
    )

    origin = RateAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = RateAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    pickup = PickupRequestSerializer(
        many=False,
        help_text="A dictionary containing information about the pickup date and time.",
        required=False
    )

    packages = RatePackageSerializer(
        many=True,
        help_text="A list containing information about packages."
    )

    carrier_options = serializers.ListField(
        child=serializers.IntegerField(min_value=API_ZERO),
        allow_empty=True,
        help_text='List of options to include in the rate request.',
        default=[]
    )

    is_dangerous_goods = serializers.BooleanField(
        help_text='Is the shipment contain dangerous goods?',
        default=False
    )

    is_metric = serializers.BooleanField(
        help_text='Is the shipment in metric units (cm and kg)?',
        default=True
    )

    is_food = serializers.BooleanField(
        help_text='Does the shipment contain food?',
        default=False
    )

    is_air = serializers.BooleanField(
        help_text='Do you want air carriers rated?',
        default=True
    )

    is_courier = serializers.BooleanField(
        help_text='Do you want courier carriers rated?',
        default=True
    )

    is_ltl = serializers.BooleanField(
        help_text='Do you want LTL carriers rated?',
        default=True
    )

    is_ftl = serializers.BooleanField(
        help_text='Do you want FTL carriers rated?',
        default=True
    )

    is_sealift = serializers.BooleanField(
        help_text='Do you want sealift carriers rated?',
        default=True
    )

    class Meta:
        fields = [
            'carrier_ids',
            'origin',
            'destination',
            'pickup',
            'packages',
            'options',
            'is_dangerous_goods',
            'is_metric',
            'is_food',
            'is_air',
            'is_courier',
            'is_ltl',
            'is_ftl',
            'is_sealift'
        ]
