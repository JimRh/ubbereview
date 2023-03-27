"""
    Title: Exchange Rate Serializers
    Description: This file will contain all functions for Exchange Rate serializers.
    Created: September 29, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import ExchangeRate


class PrivateExchangeRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExchangeRate
        fields = [
            'id',
            'exchange_rate_date',
            'expire_date',
            'source_currency',
            'target_currency',
            'exchange_rate'
        ]
