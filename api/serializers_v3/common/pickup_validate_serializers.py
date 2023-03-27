"""
    Title: Pickup Validate Serializer
    Description: This file will contain all functions for carrier markup serializers.
    Created: August 15, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers


class PickupValidateSerializer(serializers.Serializer):

    carrier_id = serializers.IntegerField(
        help_text='The Carrier id the pickup request is for.',
    )

    date = serializers.DateField(
        help_text="The pickup date in format YYYY-MM-DD.",
    )

    start_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="The start time of the pickup window.The time must be in 24-hour clock, Ex: '14:00'."
    )

    end_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="The end time of the pickup window.The time must be in 24-hour clock, Ex: '14:00'."
    )

    city = serializers.CharField(
        help_text="The city of the pickup request.",
    )
    province = serializers.CharField(
        help_text="The province/region of the pickup request. Ex: 'AB'.",
    )
    country = serializers.CharField(
        help_text="The country of the pickup request. Ex: 'CA'.",
    )
