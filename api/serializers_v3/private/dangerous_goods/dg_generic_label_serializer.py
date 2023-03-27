"""
    Title: Dangerous Good Generic Label Serializers
    Description: This file will contain all functions for Dangerous Good Generic Label serializers.
    Created: August 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodGenericLabel


class DGGenericLabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DangerousGoodGenericLabel
        fields = [
            'id',
            'name',
            'width',
            'height',
            'label'
        ]
