"""
    Title: Country  Serializers
    Description: This file will contain all functions for country serializers.
    Created: November 19, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import Country


class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = [
            'id',
            'name',
            'code',
            'currency_name',
            'currency_code',
            '_iata_name'
        ]
        extra_kwargs = {
            'name': {'validators': []},
            'code': {'validators': []},
        }
