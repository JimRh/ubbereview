"""
    Title: Ship Package Model
    Description: This file will contain functions for ship package model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import API_PACKAGE_TYPES, API_PACKAGE_ONE, API_MAX_PACK_CHAR, DIMENSION_PRECISION, \
    MAX_DIMENSION_DIGITS, WEIGHT_PRECISION, MAX_WEIGHT_DIGITS, API_CHAR_LEN, DG_PRECISION, MAX_WEIGHT_BREAK_DIGITS, \
    API_PACKAGE_CONTAINER_PACKING, API_PACKAGE_YES_NO, API_ZERO, API_MAX_CHAR_LEN
from api.serializers_v3.public.ship_commodity_serializers import ShipPackageCommoditySerializer
from api.serializers_v3.validators.package_validators import PackageDGValidator


class ShipPackageSerializer(serializers.Serializer):

    package_type = serializers.ChoiceField(
        choices=API_PACKAGE_TYPES,
        help_text="Type of package, box, skid..."
    )

    quantity = serializers.IntegerField(
        help_text='Number of packages',
        min_value=API_PACKAGE_ONE
    )

    description = serializers.CharField(
        help_text='Description of package (Be Precise)',
        max_length=API_MAX_PACK_CHAR
    )

    length = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Length of package (Individual piece)',
    )

    width = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Width of package (Individual piece)',
    )

    height = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Height of package (Individual piece)',
    )

    weight = serializers.DecimalField(
        decimal_places=WEIGHT_PRECISION,
        max_digits=MAX_WEIGHT_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Weight of package (Individual piece)',
    )

    # Optional Fields depended on package type.

    # CN ONLY Fields
    nog_id = serializers.CharField(
        help_text='Canadian North NOG ',
        max_length=API_MAX_PACK_CHAR,
        default="",
        allow_blank=True,
        required=False
    )

    # Skid Fields
    freight_class = serializers.CharField(
        help_text='NNFC Freight Class',
        max_length=API_MAX_PACK_CHAR,
        default="70.00"
    )

    # DG Fields
    is_dangerous_good = serializers.BooleanField(
        help_text='Is the package a dangerous good?',
        default=False
    )

    un_number = serializers.IntegerField(
        help_text='DG UN Number',
        default=API_ZERO
    )

    packing_group = serializers.CharField(
        help_text='DG Packing group',
        max_length=API_CHAR_LEN,
        default=""
    )

    packing_type = serializers.CharField(
        help_text='DG Packing Type',
        max_length=API_CHAR_LEN,
        default=""
    )

    proper_shipping_name = serializers.CharField(
        help_text='DG Proper Shipping Name',
        max_length=API_MAX_CHAR_LEN,
        default=""
    )

    dg_quantity = serializers.DecimalField(
        help_text='The specific quantity of dg product, separate from the packaging. 0 defines no dg.',
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        default=""
    )

    dg_nos_description = serializers.CharField(
        help_text='DG Nos Description.',
        max_length=API_CHAR_LEN,
        default=""
    )

    is_nos = serializers.BooleanField(
        help_text='Is the dg a nos?',
        default=False
    )

    is_neq = serializers.BooleanField(
        help_text='Is the dg a neq?',
        default=False
    )

    # Container Fields
    container_number = serializers.CharField(
        help_text='Container Number',
        max_length=API_CHAR_LEN,
        default=""
    )

    container_pack = serializers.ChoiceField(
        choices=API_PACKAGE_CONTAINER_PACKING,
        help_text="Container Packing Status",
        default="NA"
    )

    # Vehicle Fields
    year = serializers.CharField(
        help_text='Year the Vehicle was made in.',
        max_length=API_CHAR_LEN,
        default=""
    )

    make = serializers.CharField(
        help_text='Make of the Vehicle, IE: Ford, Chevy, GMC..',
        max_length=API_CHAR_LEN,
        default=""
    )

    vin = serializers.CharField(
        help_text='Vehicle VIN number',
        max_length=API_CHAR_LEN,
        default=""
    )

    vehicle_condition = serializers.ChoiceField(
        choices=API_PACKAGE_YES_NO,
        help_text="Is the Vehicle Running?",
        default="NA"
    )

    anti_theft = serializers.ChoiceField(
        choices=API_PACKAGE_YES_NO,
        help_text="Does the Vehicle have anti theft?",
        default="NA"
    )

    # Pharma Fields
    is_pharma = serializers.BooleanField(
        help_text='Is the package a pharma food?',
        default=False
    )

    is_cos = serializers.BooleanField(
        help_text='Does the package require chain of signature?',
        default=False
    )

    is_time_sensitive = serializers.BooleanField(
        help_text='Is the package time sensitive?',
        default=False
    )

    time_sensitive_hours = serializers.CharField(
        help_text='Number of hours in total.',
        default=""
    )

    # International Only
    commodities = ShipPackageCommoditySerializer(
        many=True,
        help_text="A list containing commodities in a packages. Sum of Weight must equal package weight.",
        allow_empty=True,
        default=[]
    )

    def validate(self, data):
        data["description"] = data["description"].strip().title()

        if data["is_dangerous_good"]:
            PackageDGValidator(data=data).valid()

        return data
