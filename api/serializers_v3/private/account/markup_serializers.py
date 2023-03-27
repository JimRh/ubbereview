"""
    Title: Markup Serializers
    Description: This file will contain all functions for markup serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Markup, Carrier, CarrierMarkup, MarkupHistory


class PrivateMarkupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Markup
        fields = [
            'id',
            'name',
            'description',
            'default_percentage',
            'default_carrier_percentage',
            'is_template'
        ]
        extra_kwargs = {
            'name': {
                'validators': []
            }
        }

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """

        carriers = Carrier.objects.all()
        markup = Markup.create(param_dict=validated_data)
        markup.save()

        for carrier in carriers:
            CarrierMarkup.create({
                "markup": markup,
                "carrier": carrier,
                "percentage": markup.default_carrier_percentage
            }).save()

        return markup

    def update(self, instance, validated_data):
        """
            Update a port.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        try:
            history = MarkupHistory.create(param_dict={
                "username": validated_data["username"],
                "old_value": instance.default_percentage,
                "new_value": Decimal(validated_data["default_percentage"]).quantize(Decimal("0.01"))
            })
            history.markup = instance
            history.save()
        except ValidationError as e:
            errors.extend([x for x in e.message_dict])
            raise ViewException(code="3709", message="Markup History: Failed to update.", errors=errors)

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance
