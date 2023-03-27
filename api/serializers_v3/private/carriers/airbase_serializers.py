"""
    Title: Private Airbase Serializers
    Description: This file will contain all functions for private airbase serializers.
    Created: November 17, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Airbase, Carrier, Province, Address
from api.serializers_v3.common.address_serializer import AddressSerializer


class PrivateAirbaseSerializer(serializers.ModelSerializer):

    not_changeable = [
        'carrier'
    ]

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the address."
    )

    class Meta:
        model = Airbase
        fields = [
            'id',
            'code',
            'address'
        ]

    def update(self, instance, validated_data):
        """
            Update airbase information for carrier.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        address = validated_data.pop("address")
        province_data = address["province"]
        province_code = province_data["code"]
        country = province_data["country"]["code"]

        try:
            province = Province.objects.get(code=province_code, country__code=country)
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f"Not found 'code': {province_code} and 'country': {country}."})
            raise ViewException(code="2110", message=f'Airbase: Province not found.', errors=errors)

        address["province"] = province
        instance.address.set_values(pairs=address)
        instance.address.save()
        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class PrivateCreateAirbaseSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code'
    )

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the address."
    )

    class Meta:
        model = Airbase
        fields = [
            "carrier_code",
            'code',
            'address'
        ]

    def create(self, validated_data):
        """
            Create new airbase for carrier
            :param validated_data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            validated_data["carrier"] = carrier
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"carrier": f"'code': {validated_data['carrier']['code']} does not exist."})
            raise ViewException(code="2111", message='Airbase: Carrier not found.', errors=errors)

        if Airbase.objects.filter(carrier=carrier, code=validated_data["code"]).exists():
            errors.append({"airbase": f"Airbase exists with {carrier.name} and {validated_data['code']}."})
            raise ViewException(code="2112", message='Airbase: Already exists.', errors=errors)

        province_data = validated_data["address"]["province"]
        province_code = province_data["code"]
        country = province_data["country"]["code"]

        try:
            province = Province.objects.get(code=province_code, country__code=country)
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f"Not found 'code': {province_code} and 'country': {country}."})
            raise ViewException(code="2113", message=f'Airbase: Province not found.', errors=errors)

        validated_data["address"]["province"] = province
        address = Address.create(param_dict=validated_data["address"])
        address.save()
        validated_data["address"] = address

        airbase = Airbase.create(param_dict=validated_data)
        airbase.save()

        return airbase
