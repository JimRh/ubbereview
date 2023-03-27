"""
    Title: Metric Goals Serializers
    Description: This file will contain all functions for Metric Goals serializers.
    Created: Jan 3, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import MetricGoals


class MetricGoalsSerializer(serializers.ModelSerializer):

    system_name = serializers.CharField(
        source='get_system_display',
        help_text='Metric System Name',
        required=False
    )

    class Meta:
        model = MetricGoals
        fields = [
            'id',
            'system',
            'system_name',
            'start_date',
            'end_date',
            'name',
            'current',
            'goal',
            'icon'
        ]
