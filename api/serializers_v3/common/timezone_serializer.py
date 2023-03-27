
"""
    Title: City Timezone Serializer
    Description: This file will contain all functions for City Timezone Serializer.
    Created: August 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import City


class CityTimezoneSerializer(serializers.ModelSerializer):

    province = serializers.CharField(
        source="province.code",
        help_text="The province/region for the city for this timezone. Ex: 'AB'.",
    )
    country = serializers.CharField(
        source="province.country.code",
        help_text="The country for the city for this timezone. Ex: 'CA'.",
    )

    class Meta:
        model = City
        fields = [
            'id',
            'name',
            'province',
            'country',
            'timezone',
            'timezone_name',
            'timezone_dst_off_set',
            'timezone_raw_off_set'
        ]
