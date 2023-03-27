
"""
    Title: Carrier Markup History Serializers
    Description: This file will contain all functions for carrier markup history serializers.
    Created: October 27, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import CarrierMarkupHistory


class PrivateCarrierMarkupHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = CarrierMarkupHistory
        fields = ['id', "change_date", 'username', "old_value", "new_value"]

