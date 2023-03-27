"""
    Title: Dangerous Good Packaging Type Serializers
    Description: This file will contain all functions for Dangerous Good packaging type serializers.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodPlacard


class DGPlacardSerializer(serializers.ModelSerializer):

    class Meta:
        model = DangerousGoodPlacard
        fields = [
            'id',
            'name',
            'background_rgb',
            'font_rgb',
            'label'

        ]
