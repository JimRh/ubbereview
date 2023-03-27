"""
    Title: Private Transit Time Serializers
    Description: This file will contain all functions for private transit time serializers.
    Created: December 02, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import TransitTime


class PrivateTransitTimeSerializer(serializers.ModelSerializer):

    class Meta:
        model = TransitTime
        fields = [
            'id',
            'origin',
            'destination',
            'rate_priority_id',
            'rate_priority_code',
            'transit_min',
            'transit_max'
        ]
