"""
    Title: Private Ship Serializers
    Description: This file will contain all functions for private ship serializers.
    Created: March 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import API_CHAR_LEN, API_MAX_CHAR_LEN, PRICE_PRECISION, MAX_PRICE_DIGITS

from api.serializers_v3.common.ship.address_serializer import ShipAddressSerializer
from api.serializers_v3.private.ship.bc_serializer import ShipBCSerializer
from api.serializers_v3.private.shipments.leg_serializers import CreateLegSerializer
from api.serializers_v3.public.ship_package_serializer import ShipPackageSerializer


class PrivateManualShipSerializer(serializers.Serializer):

    account_number = serializers.CharField(
        help_text='Account Number that the shipment belongs to.',
        required=False,
        allow_blank=True
    )

    origin = ShipAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = ShipAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    packages = ShipPackageSerializer(
        many=True,
        help_text="A list containing information about the packages."
    )

    legs = CreateLegSerializer(
        many=True,
        help_text="A list containing information about the packages."
    )

    special_instructions = serializers.CharField(
        help_text='Any additional handling or special instructions for the carrier.',
        max_length=API_MAX_CHAR_LEN,
        default="",
        allow_blank=True
    )

    reference_one = serializers.CharField(
        help_text='Reference One (Most likely to be place on documents)',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    reference_two = serializers.CharField(
        help_text='Reference Two',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    username = serializers.CharField(
        help_text='Reference Two',
        max_length=API_MAX_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    email = serializers.CharField(
        help_text='Reference Two',
        max_length=API_MAX_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    project = serializers.CharField(
        help_text='Project Reference',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    freight = serializers.DecimalField(
        help_text='Freight Cost',
        default=Decimal("0.00"),
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS
    )

    surcharge = serializers.DecimalField(
        help_text='Surcharge',
        default=Decimal("0.00"),
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS
    )

    tax = serializers.DecimalField(
        help_text='Tax',
        default=Decimal("0.00"),
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS
    )

    cost = serializers.DecimalField(
        help_text='Cost',
        default=Decimal("0.00"),
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS
    )

    bc_fields = ShipBCSerializer(
        many=False,
        help_text="A dictionary containing business central configuration details.",
        required=False
    )
