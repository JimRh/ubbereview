"""
    Title: Option Serializers
    Description: This file will contain all functions for Option serializers.
    Created: November 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import OptionName


class OptionNameSerializer(serializers.ModelSerializer):
    """
        Used to manage option names or CRUD functionality.
    """

    class Meta:
        model = OptionName
        fields = [
            'id',
            'name',
            'description',
            'is_mandatory'
        ]
        extra_kwargs = {
            'name': {'validators': []},
        }


class OptionsSerializer(serializers.ModelSerializer):
    """
        Used to populate Optional Options in ubbe shipping process
    """

    carrier_list = serializers.SerializerMethodField(
        'get_carriers',
        help_text='Carriers that have the option.',
        required=False
    )

    class Meta:
        model = OptionName
        fields = [
            'id',
            'name',
            'description',
            'carrier_list'
        ]

    @staticmethod
    def get_carriers(obj):
        carriers = obj.carrier_option_option.values_list('carrier__name', flat=True).distinct()
        return list(carriers)
