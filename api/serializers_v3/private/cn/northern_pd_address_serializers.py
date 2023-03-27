"""
    Title: Private northern pd address Serializers
    Description: This file will contain all functions for private northern pickup delivery address serializers.
    Created: December 02, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import NorthernPDAddress


class PrivateNorthernPDAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = NorthernPDAddress
        fields = [
            'id',
            'pickup_id',
            'delivery_id',
            'city_name',
            'price_per_kg',
            'min_price',
            'cutoff_weight'
        ]
