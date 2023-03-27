"""
    Title: Pickup Request Serializers
    Description: This file will contain all functions for pickup request serializer which is used for rate and ship.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from rest_framework import serializers

from api.globals.project import API_MAX_TIME_CHAR


class PickupRequestSerializer(serializers.Serializer):

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

    def validate(self, data):
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
