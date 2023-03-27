"""
    Title: Dangerous Good Ground Special Provision Serializers
    Description: This file will contain all functions for Dangerous Good Ground Special Provision serializers.
    Created: August 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodGroundSpecialProvision


class DGGroundSpecialProvisionSerializer(serializers.ModelSerializer):

    code_name = serializers.SerializerMethodField(
        'get_code_name',
        required=False
    )

    class Meta:
        model = DangerousGoodGroundSpecialProvision
        fields = [
            'id',
            'code',
            'description',
            'code_name'
        ]

    @staticmethod
    def get_code_name(obj):
        return f"{obj.code}"
