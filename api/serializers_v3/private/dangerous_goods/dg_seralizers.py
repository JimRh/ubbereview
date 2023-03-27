"""
    Title: Dangerous Good Serializers
    Description: This file will contain all functions for Dangerous Good serializers.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGood
from api.serializers_v3.private.dangerous_goods.dg_classification_serializer import DGClassificationSerializer
from api.serializers_v3.private.dangerous_goods.dg_excepted_quantity_serializer import DGExceptedQuantitySerializer
from api.serializers_v3.private.dangerous_goods.dg_packing_group_serializer import DGPackingGroupSerializer


class DGSerializer(serializers.ModelSerializer):

    classification = DGClassificationSerializer(
        many=False,
        help_text="A dictionary containing information about the classification."
    )

    packing_group = DGPackingGroupSerializer(
        many=False,
        help_text="A dictionary containing information about the packing group."
    )

    excepted_quantity = DGExceptedQuantitySerializer(
        many=False,
        help_text="A dictionary containing information about the excepted quantity."
    )

    state_name = serializers.CharField(
        source="get_state_display",
    )

    unit_measure_name = serializers.CharField(
        source="get_unit_measure_display",
    )

    class Meta:
        model = DangerousGood
        fields = [
            'id',
            'un_number',
            'short_proper_shipping_name',
            'verbose_proper_shipping_name',
            'identification_details',
            'classification',
            'subrisks',
            'specialty_label',
            'packing_group',
            'excepted_quantity',
            'unit_measure',
            'unit_measure_name',
            'air_quantity_cutoff',
            'ground_limited_quantity_cutoff',
            'ground_maximum_quantity_cutoff',
            'air_special_provisions',
            'ground_special_provisions',
            'is_gross_measure',
            'is_ground_exempt',
            'is_nos',
            'is_neq',
            'state',
            'state_name'
        ]


class CreateDGSerializer(serializers.ModelSerializer):

    class Meta:
        model = DangerousGood
        fields = [
            'un_number',
            'short_proper_shipping_name',
            'verbose_proper_shipping_name',
            'identification_details',
            'classification',
            'subrisks',
            'specialty_label',
            'packing_group',
            'excepted_quantity',
            'unit_measure',
            'air_quantity_cutoff',
            'ground_limited_quantity_cutoff',
            'ground_maximum_quantity_cutoff',
            'air_special_provisions',
            'ground_special_provisions',
            'is_gross_measure',
            'is_ground_exempt',
            'is_nos',
            'is_neq',
            'state',
        ]
        extra_kwargs = {
            'un_number': {'validators': []},
            'short_proper_shipping_name': {'validators': []},
            'packing_group': {'validators': []},
        }

    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        air_quantity_cutoff = []
        air_special_provision = []
        ground_special_provision = []
        subrisks = []

        if 'air_quantity_cutoff' in validated_data:
            air_quantity_cutoff = validated_data["air_quantity_cutoff"]
            del validated_data["air_quantity_cutoff"]

        if 'air_special_provisions' in validated_data:
            air_special_provision = validated_data["air_special_provisions"]
            del validated_data["air_special_provisions"]

        if 'ground_special_provisions' in validated_data:
            ground_special_provision = validated_data["ground_special_provisions"]
            del validated_data["ground_special_provisions"]

        if 'subrisks' in validated_data:
            subrisks = validated_data["subrisks"]
            del validated_data["subrisks"]

        dg = DangerousGood.create(param_dict=validated_data)
        dg.classification = validated_data["classification"]
        dg.excepted_quantity = validated_data["excepted_quantity"]
        dg.packing_group = validated_data["packing_group"]
        dg.save()

        dg.subrisks.set(subrisks)
        dg.air_quantity_cutoff.set(air_quantity_cutoff)
        dg.air_special_provisions.set(air_special_provision)
        dg.ground_special_provisions.set(ground_special_provision)

        dg.save()

        return dg
