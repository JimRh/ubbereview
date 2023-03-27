"""
    Title: Package Serializers
    Description: This file will contain all functions for Package serializers.
    Created: Jan 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import DEFAULT_CHAR_LEN, SHIPMENT_IDENTIFIER_LEN
from api.models import Package


class PackageSerializer(serializers.ModelSerializer):

    shipment_id = serializers.CharField(
        source="shipment.shipment_id",
        max_length=SHIPMENT_IDENTIFIER_LEN,
        help_text='Shipment ID - ubbe identification and used for tracking.'
    )

    package_type_name = serializers.CharField(
        source="get_package_type_display",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Account Shipment belongs to."
    )

    class Meta:
        model = Package
        fields = [
            'id',
            'shipment_id',
            'package_id',
            'package_account_id',
            'quantity',
            'width',
            'length',
            'height',
            'weight',
            'package_type',
            'package_type_name',
            'description',
            "freight_class_id",
            'un_number',
            'packing_group',
            'packing_type',
            'dg_proper_name',
            'dg_quantity',
            'dg_nos_description',
            'container_number',
            'container_pack',
            'vehicle_condition',
            'anti_theft',
            'year',
            'make',
            'vin',
        ]
