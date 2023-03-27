"""
    Title: Private Carrier Serializers
    Description: This file will contain all functions for private carrier serializers.
    Created: November 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import transaction
from rest_framework import serializers

from api.models import Carrier, Markup, CarrierMarkup


class PrivateCarrierSerializer(serializers.ModelSerializer):

    mode_name = serializers.CharField(
        source='get_mode_display',
        help_text='Carrier Mode Name',
        required=False
    )

    type_name = serializers.CharField(
        source='get_type_display',
        help_text='Carrier Type Name',
        required=False
    )

    class Meta:
        model = Carrier
        fields = [
            'id',
            'name',
            'code',
            'bc_vendor_code',
            'email',
            'linear_weight',
            'mode',
            'mode_name',
            'type',
            'type_name',
            'is_kilogram',
            'is_dangerous_good',
            'is_pharma'
        ]
        extra_kwargs = {
            'name': {'validators': []},
            'code': {'validators': []},
        }


class PrivateCreateCarrierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Carrier
        fields = [
            'id',
            'name',
            'code',
            'bc_vendor_code',
            'email',
            'linear_weight',
            'mode',
            'type',
            'is_kilogram',
            'is_dangerous_good',
            'is_pharma'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """

        markups = Markup.objects.all()
        carrier = Carrier.create(param_dict=validated_data)
        carrier.save()

        for markup in markups:
            CarrierMarkup.create({
                "markup": markup,
                "carrier": carrier,
                "percentage": markup.default_carrier_percentage
            }).save()

        return carrier
