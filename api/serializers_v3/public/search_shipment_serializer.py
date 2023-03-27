"""
    Title: Leg Serializers
    Description: This file will contain all functions for Leg serializers.
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import DEFAULT_CHAR_LEN, BASE_TEN, PRICE_PRECISION
from api.models import Leg, TrackingStatus
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.track_serializers import TrackSerializer
from api.serializers_v3.common.document_serializer import DocumentSerializer
from api.serializers_v3.common.surcharge_serializer import SurchargeSerializer


class SearchLegSerializer(serializers.ModelSerializer):

    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    account = serializers.CharField(
        source="shipment.subaccount.contact.company_name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Account Shipment belongs to."
    )

    account_number = serializers.CharField(
        source="shipment.subaccount.subaccount_number",
        help_text='Account id that the shipment belongs to.'
    )

    username = serializers.CharField(
        source="shipment.username",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    carrier = serializers.CharField(
        source="carrier.name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    origin = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    shipment_id = serializers.CharField(
        source="shipment.shipment_id"
    )

    account_id = serializers.CharField(
        source="shipment.account_id"
    )

    ff_number = serializers.CharField(
        source="shipment.ff_number"
    )

    project = serializers.CharField(
        source="shipment.project"
    )

    reference_one = serializers.CharField(
        source="shipment.reference_one"
    )

    reference_two = serializers.CharField(
        source="shipment.reference_two"
    )

    booking_number = serializers.CharField(
        source="shipment.booking_number"
    )

    class Meta:
        model = Leg
        fields = [
            "account",
            "account_number",
            "username",
            "shipment_id",
            "account_id",
            "ff_number",
            "project",
            "reference_one",
            "reference_two",
            "booking_number",
            'leg_id',
            'carrier',
            'service_name',
            'origin',
            'destination',
            'tracking_identifier',
            'carrier_pickup_identifier',
            'carrier_api_id',
            'ship_date',
            'is_shipped',
            'is_shipped',
            'is_delivered',
            'is_pickup_overdue',
            'is_overdue'
        ]
