"""
    Title: Dangerous Good Packaging Type Serializers
    Description: This file will contain all functions for Dangerous Good packaging type serializers.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodPackagingType


class DGPackagingTypeSerializer(serializers.ModelSerializer):

    packaging_type_name = serializers.CharField(
        source='get_packaging_type_name',
        required=False
    )

    material_name = serializers.CharField(
        source='get_material_name',
        required=False
    )

    combined = serializers.SerializerMethodField(
        'get_combined_name',
        required=False
    )

    class Meta:
        model = DangerousGoodPackagingType
        fields = [
            'id',
            'packaging_type',
            'packaging_type_name',
            'material',
            'material_name',
            'details',
            'code',
            'combined'

        ]

    @staticmethod
    def get_combined_name(obj):
        return f"{obj.get_material_display()} {obj.get_packaging_type_display()}: {obj.details}"
