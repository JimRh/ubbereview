"""
    Title: Error Code Serializers
    Description: This file will contain all functions for error code serializers.
    Created: December 07, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import ErrorCode


class PrivateErrorCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ErrorCode
        fields = [
            'id',
            'error_id',
            'creation_date',
            'updated_date',
            'system',
            'source',
            'type',
            'code',
            'name',
            'actual_message',
            'solution',
            'location'
        ]
