"""
    Title: Surcharge Serializers
    Description: This file will contain all functions for Surcharge serializers.
    Created:  Jan 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import Surcharge


class SurchargeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Surcharge
        fields = [
            'id',
            'name',
            'cost',
            'percentage',
        ]
