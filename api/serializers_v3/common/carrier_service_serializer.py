
"""
    Title: Carrier Service Serializers
    Description: This file will contain all functions for carrier service serializers.
    Created: November 15, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import CarrierService, Carrier


class CarrierServiceSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code',
        required=False
    )

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Name',
        required=False
    )

    class Meta:
        model = CarrierService
        fields = [
            'id',
            'carrier_name',
            'carrier_code',
            'name',
            'code',
            'description',
            'exceptions',
            'service_days',
            'is_international'
        ]

    def update(self, instance, validated_data):
        """
            Update City Alias for a carrier.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            del validated_data["carrier"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"carrier": f"'carrier_code' does not exist."})
            raise ViewException(code="1809", message=f'Carrier Service: Carrier not found.', errors=errors)

        instance.carrier = carrier
        instance.set_values(validated_data)
        instance.save()

        return instance
