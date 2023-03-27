"""
    Title: Dangerous Good Air Cutoff Serializers
    Description: This file will contain all functions for Dangerous Good Air Cutoff serializers.
    Created: August 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodAirCutoff


class DGAirCutoffSerializer(serializers.ModelSerializer):

    type_name = serializers.CharField(
        source="get_type_display",
    )

    air_cutoff_name = serializers.SerializerMethodField(
        'get_air_cutoff_name',
        required=False
    )

    class Meta:
        model = DangerousGoodAirCutoff
        fields = [
            'id',
            'cutoff_value',
            'packing_instruction',
            'type',
            'type_name',
            'air_cutoff_name'
        ]

    @staticmethod
    def get_air_cutoff_name(obj):
        return f"PI {obj.packing_instruction.code}: {obj.cutoff_value} {obj.get_type_display()}"
