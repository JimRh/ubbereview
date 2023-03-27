"""
    Title: Middle Location Serializers
    Description: This file will contain all functions for middle location serializers.
    Created: November 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import MiddleLocation, Province, Address
from api.serializers_v3.common.address_serializer import AddressSerializer


class PrivateMiddleLocationSerializer(serializers.ModelSerializer):

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the address.",
    )

    class Meta:
        model = MiddleLocation
        fields = [
            'id',
            'code',
            'email',
            'is_available',
            'address'
        ]
        extra_kwargs = {
            'code': {'validators': []},
        }

    @transaction.atomic()
    def create(self, validated_data):
        """
            Create new middle location.
            :param validated_data:
            :return:
        """
        errors = []
        province_data = validated_data["address"]["province"]
        code = province_data["code"]
        country = province_data["country"]["code"]

        try:
            province = Province.objects.get(code=code, country__code=country)
            validated_data["address"]["province"] = province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
            raise ViewException(code="4409", message=f'Middle Location: Province not found.', errors=errors)

        address = Address.create(param_dict=validated_data["address"])
        address.save()
        validated_data["address"] = address

        middle_location = MiddleLocation.create(validated_data)
        middle_location.save()

        return middle_location

    @transaction.atomic()
    def update(self, instance, validated_data):
        """
            Update middle location.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        if 'address' in validated_data:
            address = validated_data.pop('address')
            code = address["province"]["code"]
            country = address["province"]["country"]["code"]

            try:
                province = Province.objects.get(code=code, country__code=country)
                address["province"] = province
            except ObjectDoesNotExist:
                connection.close()
                errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
                raise ViewException(code="4410", message=f'Middle Location: Province not found.', errors=errors)

            address["province"] = province
            instance.address.set_values(pairs=address)
            instance.address.province = province
            instance.address.save()

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance
