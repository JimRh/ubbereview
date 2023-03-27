"""
    Title: Private City Alias Serializers
    Description: This file will contain all functions for private city alias serializers.
    Created: November 16, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import CityNameAlias, Carrier, Province


class PrivateCityAliasSerializer(serializers.ModelSerializer):

    province = serializers.CharField(
        source="province.code",
        help_text='Province code. Ex: AB.'
    )

    country = serializers.CharField(
        source="province.country.code",
        help_text='Country code. Ex: CA.'
    )

    class Meta:
        model = CityNameAlias
        fields = [
            'id',
            'name',
            'province',
            'country',
            'alias',
        ]

    def update(self, instance, validated_data):
        """
            Update City Alias for a carrier.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []
        province_code = validated_data["province"]["code"]
        country = validated_data["province"]["country"]["code"]

        try:
            province = Province.objects.get(code=province_code, country__code=country)
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {province_code} and 'country': {country}."})
            raise ViewException(code="2012", message="City Alias: Province not found.", errors=errors)

        instance.province = province
        instance.name = validated_data["name"]
        instance.alias = validated_data["alias"]
        instance.save()

        return instance


class PrivateCreateCityAliasSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source="carrier.code",
        help_text='Carrier Code.'
    )

    province = serializers.CharField(
        source="province.code",
        help_text='Province code. Ex: AB.'
    )

    country = serializers.CharField(
        source="province.country.code",
        help_text='Country code. Ex: CA.'
    )

    class Meta:
        model = CityNameAlias
        fields = [
            'carrier_code',
            'name',
            'province',
            'country',
            'alias',
        ]

    def create(self, validated_data):
        """
            Create City Alias for carrier.
            :param validated_data:
            :return:
        """
        errors = []
        province_code = validated_data["province"]["code"]
        country = validated_data["province"]["country"]["code"]

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            del validated_data["carrier"]
        except ObjectDoesNotExist:
            errors.append({"carrier": f"'carrier_code' does not exist."})
            raise ViewException(code="2013", message=f'City Alias: Carrier not found.', errors=errors)

        try:
            province = Province.objects.get(code=province_code, country__code=country)
            del validated_data["province"]
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {province_code} and 'country': {country}."})
            raise ViewException(code="2014", message="City Alias: Province not found.", errors=errors)

        alias = CityNameAlias.create(param_dict=validated_data)
        alias.carrier = carrier
        alias.province = province
        alias.save()

        return alias
