"""
    Title: Location Distance Serializers
    Description: This file will contain all functions for location distance serializers.
    Created: November 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, IntegrityError
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import LocationDistance, Province


class PrivateLocationDistanceSerializer(serializers.ModelSerializer):

    origin_province = serializers.CharField(
        source="origin_province.code",
        help_text='Province code. Ex: AB.'
    )

    origin_country = serializers.CharField(
        source="origin_province.country.code",
        help_text='Country code. Ex: CA.'
    )

    destination_province = serializers.CharField(
        source="destination_province.code",
        help_text='Province code. Ex: AB.'
    )

    destination_country = serializers.CharField(
        source="destination_province.country.code",
        help_text='Country code. Ex: CA.'
    )

    class Meta:
        model = LocationDistance
        fields = [
            'id',
            'origin_city',
            'origin_province',
            'origin_country',
            'destination_city',
            'destination_province',
            'destination_country',
            'distance',
            'duration'
        ]

    def create(self, validated_data):
        """
            Create new middle location.
            :param validated_data:
            :return:
        """
        errors = []
        o_code = validated_data["origin_province"]["code"]
        o_country = validated_data["origin_province"]["country"]["code"]
        d_code = validated_data["destination_province"]["code"]
        d_country = validated_data["destination_province"]["country"]["code"]

        try:
            o_province = Province.objects.get(code=o_code, country__code=o_country)
            validated_data["origin_province"] = o_province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"origin_province": f'Not found \'code\': {o_code} and \'country\': {o_country}.'})
            raise ViewException(code="4311", message="Location Distance: Province not found.", errors=errors)

        try:
            d_province = Province.objects.get(code=d_code, country__code=d_country)
            validated_data["destination_province"] = d_province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"destination_province": f'Not found \'code\': {d_code} and \'country\': {d_country}.'})
            raise ViewException(code="4312", message="Location Distance: Province not found.", errors=errors)

        distance = LocationDistance.create(validated_data)
        distance.save()

        return distance

    def update(self, instance, validated_data):
        """
            Update middle location.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []
        o_code = validated_data["origin_province"]["code"]
        o_country = validated_data["origin_province"]["country"]["code"]
        d_code = validated_data["destination_province"]["code"]
        d_country = validated_data["destination_province"]["country"]["code"]

        try:
            o_province = Province.objects.get(code=o_code, country__code=o_country)
            validated_data["origin_province"] = o_province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"origin_province": f'Not found \'code\': {o_code} and \'country\': {o_country}.'})
            raise ViewException(code="4313", message="Location Distance: Province not found.", errors=errors)

        try:
            d_province = Province.objects.get(code=d_code, country__code=d_country)
            validated_data["destination_province"] = d_province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"destination_province": f'Not found \'code\': {d_code} and \'country\': {d_country}.'})
            raise ViewException(code="4314", message="Location Distance: Province not found.", errors=errors)

        try:
            instance.set_values(pairs=validated_data)
            instance.origin_province = o_province
            instance.d_province = d_province
            instance.save()
        except IntegrityError:
            connection.close()
            errors.append({"location_distance": f'Already exists.'})
            raise ViewException(code="4315", message="Location Distance: Already Exists.", errors=errors)

        return instance


class CheckLocationDistanceSerializer(serializers.ModelSerializer):
    origin_province = serializers.CharField(
        source="origin_province.code",
        help_text='Province code. Ex: AB.'
    )
    origin_country = serializers.CharField(
        source="origin_province.country.code",
        help_text='Country code. Ex: CA.'
    )
    destination_province = serializers.CharField(
        source="destination_province.code",
        help_text='Province code. Ex: AB.'
    )
    destination_country = serializers.CharField(
        source="destination_province.country.code",
        help_text='Country code. Ex: CA.'
    )

    class Meta:
        model = LocationDistance
        read_only_fields = ['distance', 'duration']
        fields = [
            'id',
            'origin_city',
            'origin_province',
            'origin_country',
            'destination_city',
            'destination_province',
            'destination_country',
            'distance',
            'duration'
        ]
