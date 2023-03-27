"""
    Title: Airport Serializers
    Description: This file will contain all functions for airport serializers.
    Created: November 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import Airport
from api.serializers_v3.common.address_serializer import AddressSerializer


class PrivateAirportSerializer(serializers.ModelSerializer):

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the address.",
        required=False,
    )

    class Meta:
        model = Airport
        fields = [
            'id',
            'name',
            'code',
            'address'
        ]
