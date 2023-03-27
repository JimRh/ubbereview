"""
    Title: Cancel Shipment Serializers
    Description: This file will contain all functions for Cancel serializers
    Created: Nov 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.globals.project import ID_LENGTH, LEG_ID_LENGTH


class CancelSerializer(serializers.Serializer):

    shipment_id = serializers.RegexField(
        max_length=ID_LENGTH,
        min_length=ID_LENGTH,
        required=False,
        regex=r'^(ub)(\d{10})$',
        help_text="'shipment_id must be in format: 'ub0123456789'."

    )

    leg_id = serializers.RegexField(
        max_length=LEG_ID_LENGTH,
        min_length=LEG_ID_LENGTH,
        required=False,
        regex=r'^(ub)(\d{10})(\w{1})$'
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
