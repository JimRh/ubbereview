"""
    Title: Dangerous Good Classification Serializers
    Description: This file will contain all functions for Dangerous Good Classification serializers.
    Created: August 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodClassification


class DGClassificationSerializer(serializers.ModelSerializer):

    classification_name = serializers.SerializerMethodField(
        'get_classification_name',
        required=False
    )

    class Meta:
        model = DangerousGoodClassification
        fields = [
            'id',
            'classification',
            'classification_name',
            'division',
            'class_name',
            'division_characteristics',
            'label',
        ]

    @staticmethod
    def get_classification_name(obj):
        return f"{obj.classification}.{obj.division} {obj.class_name}"
