"""
    Title: Pickup Serializers
    Description: This file will contain all functions for pickup serializer.
    Created: February 8, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import datetime

from rest_framework import serializers

from api.apis.pickup.pickup import Pickup
from api.globals.project import API_MAX_TIME_CHAR, API_MAX_CHAR_LEN, LEG_IDENTIFIER_LEN
from api.models import Leg


class PickupSerializer(serializers.Serializer):

    leg_id = serializers.RegexField(
        regex='^(ub)(\\d{10})[MPD]$',
        max_length=LEG_IDENTIFIER_LEN,
        help_text="Leg id to book pickup for. Format 'ub123456789X' with one of 'M, P,,D' for X."
    )

    date = serializers.DateField(
        help_text="The pickup date in format YYYY-MM-DD. (UTC)",
    )

    start_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=API_MAX_TIME_CHAR,
        min_length=API_MAX_TIME_CHAR,
        help_text="The start time of the pickup window. The time must be in 24-hour clock, Ex: '14:00'."
    )

    end_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=API_MAX_TIME_CHAR,
        min_length=API_MAX_TIME_CHAR,
        help_text="The end time of the pickup window.The time must be in 24-hour clock, Ex: '14:00'."
    )

    special_instructions = serializers.CharField(
        default="",
        allow_blank=True,
        max_length=API_MAX_CHAR_LEN,
        help_text="Any special instructions for the pickup?"
    )

    def validate(self, data):
        """

        :param data:
        :return:
        """

        if not Leg.objects.filter(leg_id=data["leg_id"]).exists():
            raise serializers.ValidationError({'leg_id': [f"Leg not found."]})

        now_date = datetime.datetime.now().date()

        if now_date > data["date"]:
            raise serializers.ValidationError({'date': [f'This field cannot be in the past.']})

        start_split = data["start_time"].split(":")
        end_split = data["end_time"].split(":")

        start_time = datetime.time(hour=int(start_split[0]), minute=int(start_split[1]))
        end_time = datetime.time(hour=int(end_split[0]), minute=int(end_split[1]))

        if end_time < start_time:
            raise serializers.ValidationError({'end_time': [f'This field cannot be before start time.']})

        return data

    def create(self, validated_data):
        """

        :param validated_data:
        :return:
        """

        pickup = Pickup(ubbe_request=validated_data).pickup()

        return pickup

    def update(self, instance, validated_data):
        """
        Update Pickup number by canceling and rebooking the pickup.
        :param instance:
        :param validated_data:
        :return:
        """

        pickup = Pickup(ubbe_request=validated_data)
        ret = pickup.update()

        return ret


class CancelPickupSerializer(serializers.Serializer):

    leg_id = serializers.RegexField(
        regex='^(ub)(\\d{10})[MPD]$',
        max_length=LEG_IDENTIFIER_LEN,
        help_text="Leg id to book pickup for. Format 'ub123456789X' with one of 'M, P,,D' for X."
    )

    reason = serializers.CharField(
        default="",
        max_length=API_MAX_CHAR_LEN,
        help_text="Reason to cancel pickup?"
    )

    def validate(self, data):
        """

        :param data:
        :return:
        """

        if not Leg.objects.filter(leg_id=data["leg_id"]).exists():
            raise serializers.ValidationError({'leg_id': [f"Leg not found."]})

        return data
