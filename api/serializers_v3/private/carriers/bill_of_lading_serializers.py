"""
    Title: Private Bill Of Lading Serializers
    Description: This file will contain all functions for private Bill Of Lading serializers.
    Created: November 16, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import BillOfLading, Dispatch


class PrivateBillOfLadingSerializer(serializers.ModelSerializer):
    not_changeable = [
        'dispatch', 'carrier'
    ]

    dispatch_id = serializers.IntegerField(
        source='dispatch.id',
        help_text='Dispatch id',
        required=False
    )

    dispatch_location = serializers.CharField(
        source='dispatch.location',
        help_text='Dispatch Location',
        required=False
    )

    carrier_code = serializers.IntegerField(
        source='dispatch.carrier.code',
        help_text='Carrier Code',
        required=False
    )

    carrier_name = serializers.CharField(
        source='dispatch.carrier.name',
        help_text='Carrier Name',
        required=False
    )

    class Meta:
        model = BillOfLading
        fields = [
            'id',
            'dispatch_id',
            'dispatch_location',
            'carrier_code',
            'carrier_name',
            'bill_of_lading',
            'is_available'
        ]

    def update(self, instance, validated_data):
        """
            Update bill of lading.
            :param instance:
            :param validated_data:
            :return:
        """
        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class PrivateCreateBillOfLadingSerializer(serializers.ModelSerializer):

    dispatch_id = serializers.IntegerField(
        source='dispatch.id',
        help_text='Dispatch id',
        required=False
    )

    class Meta:
        model = BillOfLading
        fields = [
            'dispatch_id',
            'bill_of_lading',
        ]

    def create(self, validated_data):
        """
            Create new carrier service level
            :param validated_data:
            :return:
        """

        try:
            dispatch = Dispatch.objects.get(pk=validated_data["dispatch"]["id"])
            validated_data["dispatch"] = dispatch
        except ObjectDoesNotExist:
            connection.close()
            errors = [{"carrier": f"'code' does not exist."}]
            raise ViewException(code="2209", message=f'Bill of Lading: Carrier not found.', errors=errors)

        bol = BillOfLading.create(param_dict=validated_data)
        bol.save()

        return bol
