"""
    Title: Dangerous Good Packing Group Serializers
    Description: This file will contain all functions for Dangerous Good Packing Group serializers.
    Created: August 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodPackingGroup


class DGPackingGroupSerializer(serializers.ModelSerializer):

    packing_group_name = serializers.CharField(
        source="get_packing_group_display",
    )

    combined = serializers.SerializerMethodField(
        'get_combined_name',
        required=False
    )

    class Meta:
        model = DangerousGoodPackingGroup
        fields = [
            'id',
            'packing_group',
            'packing_group_name',
            'description',
            'combined'
        ]

    @staticmethod
    def get_combined_name(obj):
        return f"{obj.get_packing_group_display()}: {obj.description}"


class CreateDGPackingGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = DangerousGoodPackingGroup
        fields = [
            'packing_group',
            'description'
        ]
