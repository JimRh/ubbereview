"""
    Title: Carrier Pickup Serializer
    Description: This file will contain all functions for carrier pickup serializers.
    Created: November 17, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Carrier, CarrierPickupRestriction


class PickupRestrictionSerializer(serializers.ModelSerializer):
    not_changeable = [
        'carrier'
    ]

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Name',
        required=False
    )

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code',
    )

    min_start_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="The time should be in Military Time, Ex: '14:00'. Used for dropdown min time."
    )

    max_start_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="The time should be in Military Time, Ex: '14:00'."
    )

    min_end_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="The time should be in Military Time, Ex: '14:00'."
    )

    max_end_time = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="The time should be in Military Time, Ex: '14:00'. Used for dropdown max time."
    )

    min_time_same_day = serializers.RegexField(
        regex='^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
        max_length=5,
        min_length=5,
        help_text="Minimum time for same day pickup for the carrier. The time should be in Military Time, Ex: '14:00'."
    )

    class Meta:
        model = CarrierPickupRestriction
        fields = [
            'id',
            'carrier_name',
            'carrier_code',
            'min_start_time',
            'max_start_time',
            'min_end_time',
            'max_end_time',
            'pickup_window',
            'min_time_same_day',
            'max_pickup_days'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
        except ObjectDoesNotExist:
            errors = [{"carrier": f"'carrier_code' does not exist."}]
            raise ViewException(code="2303", message=f'Pickup Restriction: Carrier not found.', errors=errors)

        del validated_data['carrier']
        carrier_pickup = CarrierPickupRestriction.create(param_dict=validated_data)
        carrier_pickup.carrier = carrier
        carrier_pickup.save()

        return carrier_pickup

    def update(self, instance, validated_data):
        """
            :param instance:
            :param validated_data:
            :return:
        """
        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance
