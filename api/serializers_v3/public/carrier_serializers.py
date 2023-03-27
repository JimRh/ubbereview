
"""
    Title: Public Carrier Serializers
    Description: This file will contain all functions for public carrier serializers.
    Created: November 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import Carrier


class PublicCarrierSerializer(serializers.ModelSerializer):

    mode = serializers.CharField(
        source='get_mode_display',
        help_text='Carrier Mode Name',
        required=False
    )

    type = serializers.CharField(
        source='get_type_display',
        help_text='Carrier Type Name',
        required=False
    )

    class Meta:
        model = Carrier
        fields = [
            'id',
            'name',
            'code',
            'linear_weight',
            'mode',
            'type',
            'is_kilogram',
            'is_dangerous_good',
            'is_pharma'
        ]

