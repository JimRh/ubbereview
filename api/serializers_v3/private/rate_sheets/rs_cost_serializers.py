"""
    Title: Rate Sheet Lane Serializers
    Description: This file will contain all functions for rate sheet lane serializers.
    Created: October 13, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import RateSheetLane, RateSheet


class RateSheetCostSerializer(serializers.ModelSerializer):
    not_changeable = [
        'rate_sheet'
    ]

    rate_sheet_id = serializers.IntegerField(
        source='rate_sheet.id',
        help_text='Rate Sheet Lane',
        required=True
    )

    carrier_code = serializers.IntegerField(
        source='rate_sheet.carrier.code',
        help_text='Carrier Code Lane',
        required=True
    )

    class Meta:
        model = RateSheetLane
        fields = [
            'id',
            'rate_sheet_id',
            'carrier_code',
            'min_value',
            'max_value',
            'cost'
        ]

    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []

        try:
            rate_sheet = RateSheet.objects.get(
                pk=validated_data["rate_sheet"]["id"],
                carrier__code=validated_data["rate_sheet"]["carrier"]["code"]
            )
        except ObjectDoesNotExist as e:
            connection.close()
            errors.append({"rate_sheet_cost": e})
            raise ViewException(
                code="6309", message=f"RateSheetCost: Not found with {validated_data['rate_sheet_id']}.", errors=errors
            )

        min_val = validated_data["min_value"]
        max_val = validated_data["max_value"]
        exists = RateSheetLane.objects.filter(rate_sheet=rate_sheet, min_value=min_val, max_value=max_val).exists()

        if exists:
            errors.append({"rate_sheet_cost": f"Weight break already exists for {min_val} to {max_val}."})
            raise ViewException(code="6310", message=f"RateSheetCost: Weight break already exists.", errors=errors)

        rate_sheet_lane = RateSheetLane.create(param_dict=validated_data)
        rate_sheet_lane.rate_sheet = rate_sheet
        rate_sheet_lane.save()

        return rate_sheet_lane

    def update(self, instance, validated_data):
        """
            :param instance:
            :param validated_data:
            :return:
        """
        rate_sheet_data = validated_data.pop("rate_sheet")

        instance.set_values(pairs=rate_sheet_data)
        instance.save()

        return instance
