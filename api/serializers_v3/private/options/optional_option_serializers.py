"""
    Title: Optional Options Serializers
    Description: This file will contain all functions for Optional Options serializers.
    Created: November 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import CarrierOption, Carrier, OptionName


class OptionalOptionsSerializer(serializers.ModelSerializer):
    """
        Used to manage option names or CRUD functionality.
    """
    not_changeable = [
        'id', 'option_name', 'carrier', "option", "carrier"
    ]

    carrier = serializers.CharField(
        source="carrier.name",
        help_text="Carrier Name.",
        required=False
    )

    option_name = serializers.CharField(
        source="option.name",
        help_text="Option Name.",
        required=False
    )

    class Meta:
        model = CarrierOption
        fields = [
            'id',
            'option_name',
            'carrier',
            'evaluation_expression',
            'minimum_value',
            'maximum_value',
            'percentage',
            'start_date',
            'end_date',
        ]

    def update(self, instance, validated_data):
        """
            Update a optional option.
            :param instance:
            :param validated_data:
            :return:
        """

        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class CreateOptionalOptionsSerializer(serializers.ModelSerializer):
    """
        Used to create an optional option.
    """

    carrier_code = serializers.IntegerField(
        source="carrier.code",
        help_text="Carrier Code"
    )

    option_id = serializers.CharField(
        source="option.id",
        help_text="Option id.",
        required=False
    )

    class Meta:
        model = CarrierOption
        fields = [
            'option_id',
            'carrier_code',
            'evaluation_expression',
            'minimum_value',
            'maximum_value',
            'percentage',
            'start_date',
            'end_date',
        ]

    def create(self, validated_data):
        """
            Create new optional option for a carrier.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            option = OptionName.objects.get(id=validated_data["option"]["id"])
            del validated_data["option"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"option_id": f"'option_id' does not exist."})
            raise ViewException(code="2506", message=f"Optional Option: 'option_id' does not exist.", errors=errors)

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            del validated_data["carrier"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"carrier_code": f"'carrier_code' does not exist."})
            raise ViewException(code="2507", message=f"Optional Option: 'carrier_code' does not exist.", errors=errors)

        optional = CarrierOption.create(param_dict=validated_data)
        optional.option = option
        optional.carrier = carrier
        optional.save()

        return optional
