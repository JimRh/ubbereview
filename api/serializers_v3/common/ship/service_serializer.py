"""
    Title: Ship Service Serializers
    Description: This file will contain all functions for ship service serializers.
    Created: March 22, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import API_ZERO, ISO_3166_1_LEN


class PDServiceSerializer(serializers.Serializer):

    carrier_id = serializers.IntegerField(
        min_value=API_ZERO,
        help_text="Carrier id for main leg of the shipment."
    )

    service_code = serializers.CharField(
        help_text='Service code for carrier service level',
    )


class ServiceSerializer(serializers.Serializer):

    carrier_id = serializers.IntegerField(
        min_value=API_ZERO,
        help_text="Carrier id for main leg of the shipment."
    )

    service_code = serializers.CharField(
        help_text='Service code for carrier service level',
    )

    origin_base = serializers.CharField(
        help_text='Origin airport/port base: ISO Code (Ex. YEG)',
        max_length=ISO_3166_1_LEN,
        default="",
        allow_blank=True
    )

    destination_base = serializers.CharField(
        help_text='Destination airport/port base: ISO Code (Ex. YEG)',
        max_length=ISO_3166_1_LEN,
        default="",
        allow_blank=True
    )

    middle_base = serializers.CharField(
        help_text='Interline location: ISO Code (Ex. YEG)',
        max_length=ISO_3166_1_LEN,
        default="",
        allow_blank=True
    )

    pickup = PDServiceSerializer(
        help_text="Pickup Carrier Information for Multi Modal Logic",
        required=False
    )

    delivery = PDServiceSerializer(
        help_text="Delivery Carrier Information for Multi Modal Logic",
        required=False
    )
