"""
    Title: Port Serializers
    Description: This file will contain all functions for Port serializers.
    Created: November 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Port, Province, Address
from api.serializers_v3.common.address_serializer import AddressSerializer


class PrivatePortSerializer(serializers.ModelSerializer):

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the port address."
    )

    class Meta:
        model = Port
        fields = [
            'id',
            'name',
            'code',
            'address',
        ]

    def create(self, validated_data):
        """
            Create New Fuel Surcharge.
            :param validated_data:
            :return:
        """
        errors = []

        code = validated_data["address"]["province"]["code"]
        country = validated_data["address"]["province"]["country"]["code"]

        try:
            province = Province.objects.get(code=code, country__code=country)
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
            raise ViewException(code="4609", message=f'Port: Province not found.', errors=errors)

        validated_data["address"]["province"] = province

        address = Address.create(param_dict=validated_data["address"])
        address.save()

        validated_data["address"] = address

        port = Port.create(param_dict=validated_data)
        port.save()

        return port

    def update(self, instance, validated_data):
        """
            Update a port.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        code = validated_data["address"]["province"]["code"]
        country = validated_data["address"]["province"]["country"]["code"]

        try:
            province = Province.objects.get(code=code, country__code=country)
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
            raise ViewException(code="4610", message=f'Port: Province not found.', errors=errors)

        validated_data["address"]["province"] = province
        address_data = validated_data.pop("address")

        instance.address.province = province
        instance.address.set_values(pairs=address_data)
        instance.address.save()

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance
