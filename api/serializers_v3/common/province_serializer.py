"""
    Title: Province  Serializers
    Description: This file will contain all functions for province serializers.
    Created: November 19, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Province, Country
from api.serializers_v3.common.country_serializer import CountrySerializer


class ProvinceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Province
        fields = [
            'id',
            'name',
            'code',
        ]

    def create(self, validated_data):
        """
            Create new province for a country.
            :param validated_data:
            :return:
        """
        errors = []
        code = validated_data['code']
        country = validated_data.pop('country')

        if Province.objects.filter(code=code, country__code=country).exists():
            errors.append({"shipment": f"Province already exists for Code: {code} and Country: {country}"})
            raise ViewException(code="1508", message=f'Province: Province already exists.', errors=errors)

        try:
            country = Country.objects.get(code=country)
        except ObjectDoesNotExist:
            errors.append({"country": f"Country not found: {country}"})
            raise ViewException(code="1509", message=f'Province: Country not found.', errors=errors)

        province = Province.create(param_dict=validated_data)
        province.country = country
        province.save()

        return province


class ProvinceDetailSerializer(serializers.ModelSerializer):

    country = CountrySerializer(
        many=False,
        help_text="A dictionary containing information about the country.",
        required=False
    )

    class Meta:
        model = Province
        fields = [
            'id',
            'name',
            'code',
            'country'
        ]

