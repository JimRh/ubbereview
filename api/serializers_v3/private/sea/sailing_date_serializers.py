"""
    Title: Sailing Date Serializers
    Description: This file will contain all functions for Port serializers.
    Created: April 21, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_CHAR_LEN
from api.models import SealiftSailingDates, Carrier, Port
from api.serializers_v3.private.sea.port_serializers import PrivatePortSerializer


class PrivateSailingDateSerializer(serializers.ModelSerializer):

    carrier_name = serializers.CharField(
        source="carrier.name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name.",
        required=False
    )

    carrier_code = serializers.IntegerField(
        source="carrier.code",
        help_text="Carrier Code.",
    )

    port = PrivatePortSerializer(
        many=False,
        help_text="A dictionary containing information about the port address."
    )

    long_name = serializers.CharField(
        source="get_name_display",
        help_text="Sailing Date Long Name.",
        required=False
    )

    status_name = serializers.CharField(
        source="get_status_display",
        help_text="Sailing Date Status Name.",
        required=False
    )

    class Meta:
        model = SealiftSailingDates
        fields = [
            'id',
            'carrier_name',
            'carrier_code',
            'port',
            'name',
            'long_name',
            'sailing_date',
            'dg_packing_cutoff',
            'cargo_packing_cutoff',
            'bbe_dg_cutoff',
            'bbe_cargo_cutoff',
            'weight_capacity',
            'current_weight',
            'status',
            'status_name',
            'port_destinations'
        ]


class PrivateCreateSailingDateSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source="carrier.code",
        help_text="Carrier Code.",
    )

    class Meta:
        model = SealiftSailingDates
        fields = [
            'carrier_code',
            'port',
            'name',
            'sailing_date',
            'dg_packing_cutoff',
            'cargo_packing_cutoff',
            'bbe_dg_cutoff',
            'bbe_cargo_cutoff',
            'weight_capacity',
            'current_weight',
            'status',
            'port_destinations'
        ]

    def create(self, validated_data):
        """
            Create New Sailing Date.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
        except ObjectDoesNotExist:
            errors.append({"carrier": f'Not found \'code\': {validated_data["carrier"]["code"]}.'})
            raise ViewException(code="8002", message=f'Port: Province not found.', errors=errors)

        validated_data["carrier"] = carrier

        sailing = SealiftSailingDates.create(param_dict=validated_data)
        sailing.save()
        sailing.port_destinations.add(*validated_data["port_destinations"])
        sailing.save()

        return sailing

    def update(self, instance, validated_data):
        """
            Update Sailing Date.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        if "carrier" in validated_data:
            carrier = validated_data.pop("carrier")

            try:
                carrier = Carrier.objects.get(code=carrier["code"])
            except ObjectDoesNotExist:
                errors.append({"carrier": f'Not found \'code\': {validated_data["carrier"]["code"]}.'})
                raise ViewException(code="8002", message=f'Port: Province not found.', errors=errors)

            instance.carrier = carrier

        if "port_destinations" in validated_data:
            instance.port_destinations.set(validated_data.pop("port_destinations"))

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance
