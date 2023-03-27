
"""
    Title: Create Carrier Service Serializers
    Description: This file will contain all functions for create carrier service serializers.
    Created: November 15, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, IntegrityError
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import CarrierService, Carrier


class PrivateCreateCarrierServiceSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code',
    )

    class Meta:
        model = CarrierService
        fields = [
            'carrier_code',
            'name',
            'code',
            'description',
            'exceptions',
            'service_days',
            'is_international'
        ]

    def create(self, validated_data):
        """
            Create new carrier service level
            :param validated_data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            del validated_data["carrier"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"carrier": f"'code' does not exist."})
            raise ViewException(code="1809", message=f'Carrier Service: Carrier not found.', errors=errors)

        try:
            service = CarrierService.create(param_dict=validated_data)
            service.carrier = carrier
            service.save()
        except IntegrityError:
            connection.close()
            errors.append({"carrier": f"'carrier' and 'carrier_code' may already exist."})
            raise ViewException(code="1810", message=f'Carrier Service: Already exists.', errors=errors)

        return service
