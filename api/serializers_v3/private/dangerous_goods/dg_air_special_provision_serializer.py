"""
    Title: Dangerous Good Air Special Provision Serializers
    Description: This file will contain all functions for Dangerous Good Air Special Provision serializers.
    Created: August 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodAirSpecialProvision


class DGAirSpecialProvisionSerializer(serializers.ModelSerializer):

    code_name = serializers.SerializerMethodField(
        'get_code_name',
        required=False
    )

    class Meta:
        model = DangerousGoodAirSpecialProvision
        fields = [
            'id',
            'code',
            'note',
            'description',
            'is_non_restricted',
            'code_name'
        ]

    @staticmethod
    def get_code_name(obj):
        return f"A{obj.code}"
