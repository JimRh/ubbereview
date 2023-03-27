"""
    Title: Api Serializers
    Description: This file will contain all functions for api serializers.
    Created: November 19, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import API


class PrivateApiSerializer(serializers.ModelSerializer):

    class Meta:
        model = API
        fields = [
            'id',
            'name',
            'active',
            'category'
        ]
        extra_kwargs = {
            'name': {'validators': []},
        }
