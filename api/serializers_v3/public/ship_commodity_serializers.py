"""
    Title: Ship Package Commodity Model
    Description: This file will contain functions for ship package commodity model.
    Created: November 29, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import API_PACKAGE_ONE, API_MAX_PACK_CHAR, DIMENSION_PRECISION, \
    MAX_DIMENSION_DIGITS, WEIGHT_PRECISION, MAX_WEIGHT_DIGITS, API_COUNTRY_CODE_LEN


class ShipPackageCommoditySerializer(serializers.Serializer):

    quantity = serializers.IntegerField(
        help_text='Number of goods in packages',
        min_value=API_PACKAGE_ONE
    )

    description = serializers.CharField(
        help_text='Description of the good. (Be Precise and accurate)',
        max_length=API_MAX_PACK_CHAR
    )

    made_in_country_code = serializers.CharField(
        help_text='Country of manufacture. IE: CA, US, MX',
        max_length=API_COUNTRY_CODE_LEN,
        min_length=API_COUNTRY_CODE_LEN,
    )

    quantity_unit_of_measure = serializers.CharField(
        help_text='Must be Each',
        default="Each"
    )

    unit_value = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("0.00"),
        help_text='Cost of good',
    )

    total_weight = serializers.DecimalField(
        decimal_places=WEIGHT_PRECISION,
        max_digits=MAX_WEIGHT_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Weight of good',
    )
