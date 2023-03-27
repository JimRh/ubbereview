"""
    Title: Package Serializers
    Description: This file will contain all functions for Package serializers.
    Created: Aug 08, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal
from django.db import connection

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_CHAR_LEN, SHIPMENT_IDENTIFIER_LEN, BASE_TEN, PRICE_PRECISION, MAX_PACK_ID_LEN
from api.models import Package, Shipment


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
            'shipment',
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


class CreatePackageSerializer(serializers.ModelSerializer):
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

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
            'shipment_id',
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
            'is_cooler',
            'is_frozen',
            'is_pharma',
            'time_sensitive_hours'

        ]

    def create(self, validated_data):
        """
            Create New Shipment.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            shipment = Shipment.objects.get(shipment_id=validated_data["shipment"]["shipment_id"])
        except ObjectDoesNotExist as e:
            connection.close()
            errors.append({"package": "shipment_id not found."})
            raise ViewException(code="1209", message="Package: shipment_id not found.", errors=errors)

        instance = Package.create(param_dict=validated_data)
        instance.shipment = shipment
        instance.save()

        return instance
