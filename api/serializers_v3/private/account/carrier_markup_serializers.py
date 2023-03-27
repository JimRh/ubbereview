"""
    Title: Carrier Markup Serializers
    Description: This file will contain all functions for carrier markup serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import CarrierMarkup, CarrierMarkupHistory


class PrivateCarrierMarkupSerializer(serializers.ModelSerializer):

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Name',
        required=False
    )

    carrier_mode = serializers.CharField(
        source='carrier.get_mode_display',
        help_text='Carrier Mode Name',
        required=False
    )

    class Meta:
        model = CarrierMarkup
        fields = [
            'id',
            'carrier_name',
            'carrier_mode',
            'percentage'
        ]


class PrivateUpdateCarrierMarkupSerializer(serializers.ModelSerializer):

    markup_id = serializers.IntegerField(
        source='markup.id',
        help_text='Markup ID',
        required=False
    )

    username = serializers.CharField(
        help_text='Username for changes the markup',
    )

    class Meta:
        model = CarrierMarkup
        fields = [
            'id',
            'markup_id',
            'username',
            'percentage'
        ]

    def update(self, instance, validated_data):
        """
            Update a carrier markup.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        try:
            history = CarrierMarkupHistory.create(param_dict={
                "username": validated_data["username"],
                "old_value": instance.percentage,
                "new_value": Decimal(validated_data["percentage"]).quantize(Decimal("0.01"))
            })
            history.carrier_markup = instance
            history.save()
        except ValidationError as e:
            errors.extend([x for x in e.message_dict])
            raise ViewException(code="3907", message="Carrier Markup History: Failed to update.", errors=errors)

        instance.percentage = Decimal(validated_data["percentage"]).quantize(Decimal("0.01"))
        instance.save()

        return instance

