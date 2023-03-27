"""
    Title: Api Serializers
    Description: This file will contain all functions for api serializers.
    Created: February 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import ApiPermissions


class PrivateApiPermissionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiPermissions
        fields = [
            'id',
            'name',
            'permissions',
            'category',
            'reason',
            'is_active',
            'is_admin'
        ]
        extra_kwargs = {
            'name': {'validators': []},
        }
