"""
    Title: Fuel Surcharge Serializers
    Description: This file will contain all functions for fuel surcharge serializers.
    Created: November 16, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import FuelSurcharge, Carrier


class PrivateFuelSurchargeSerializer(serializers.ModelSerializer):

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Name',
        required=False
    )
    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code'
    )

    fuel_type_name = serializers.CharField(
        source='get_fuel_type_display',
        help_text='Fuel Type Name: Domestic or International',
        required=False
    )

    class Meta:
        model = FuelSurcharge
        fields = [
            'id',
            'carrier_name',
            'carrier_code',
            'fuel_type',
            'fuel_type_name',
            'updated_date',
            'ten_thou_under',
            'ten_thou_to_fifty_five_thou',
            'fifty_five_thou_greater'
        ]


class PrivateCreateFuelSurchargeSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code'
    )

    class Meta:
        model = FuelSurcharge
        fields = [
            'carrier_code',
            'fuel_type',
            'updated_date',
            'ten_thou_under',
            'ten_thou_to_fifty_five_thou',
            'fifty_five_thou_greater'
        ]

    def create(self, validated_data):
        """
            Create New Fuel Surcharge.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
        except ObjectDoesNotExist as e:
            errors.append({"carrier": "'carrier_code' does not exist."})
            raise ViewException(code="1708", message="Fuel Surcharge: Carrier not found.", errors=errors)

        if FuelSurcharge.objects.filter(carrier=carrier, fuel_type=validated_data["fuel_type"]).exists():
            errors.append({"fuel_surcharge": f"Already exists with {carrier.name} and {validated_data['fuel_type']}"})
            raise ViewException(code="1709", message="Fuel Surcharge: Already Exists.", errors=errors)

        fuel = FuelSurcharge.create(param_dict=validated_data)
        fuel.carrier = carrier
        fuel.save()

        return fuel
