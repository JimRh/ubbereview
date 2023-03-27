"""
    Title: Postal Codee Validate Serializer
    Description: This file will contain all functions for postal code serializers.
    Created: Sept 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers


class PostalCodeValidateSerializer(serializers.Serializer):

    city = serializers.CharField(
        help_text="Location city name.",
    )
    postal_code = serializers.CharField(
        help_text="Postal Code for city.",
    )
    province = serializers.CharField(
        help_text="The province/region of city. Ex: 'AB'.",
    )
    country = serializers.CharField(
        help_text="The country of city. Ex: 'CA'.",
    )
