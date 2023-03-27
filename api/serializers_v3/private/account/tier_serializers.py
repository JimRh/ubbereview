"""
    Title: Port Serializers
    Description: This file will contain all functions for Port serializers.
    Created: November 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import AccountTier


class PrivateTierSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountTier
        fields = [
            'id',
            'name',
            'base_cost',
            'user_cost',
            'shipment_cost',
            'carrier_cost',
            'api_requests_per_minute_cost',
            'user_count',
            'shipment_count',
            'carrier_count',
            'api_requests_per_minute_count',
            'additional_user_count',
            'additional_shipment_count',
            'additional_carrier_count',
            'additional_api_requests_count',
            'permissions'
        ]
