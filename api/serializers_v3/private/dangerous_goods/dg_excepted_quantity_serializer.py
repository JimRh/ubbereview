"""
    Title: Dangerous Good Excepted Quantity Serializers
    Description: This file will contain all functions for Dangerous Good Excepted Quantity serializers.
    Created: August 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodExceptedQuantity


class DGExceptedQuantitySerializer(serializers.ModelSerializer):

    excepted_quantity_name = serializers.SerializerMethodField(
        'get_excepted_quantity_name',
        required=False
    )

    class Meta:
        model = DangerousGoodExceptedQuantity
        fields = [
            'id',
            'excepted_quantity_code',
            'excepted_quantity_name',
            'inner_cutoff_value',
            'outer_cutoff_value'
        ]

    @staticmethod
    def get_excepted_quantity_name(obj):
        return f"E{obj.excepted_quantity_code}"
