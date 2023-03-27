"""
    Title: Leg Serializers
    Description: This file will contain all functions for Leg serializers.
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import DEFAULT_CHAR_LEN, BASE_TEN, PRICE_PRECISION
from api.models import Leg, TrackingStatus
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.track_serializers import TrackSerializer
from api.serializers_v3.common.document_serializer import DocumentSerializer
from api.serializers_v3.common.surcharge_serializer import SurchargeSerializer


class PublicLegSerializer(serializers.ModelSerializer):
    not_changeable = [
        'id', 'sub_account', 'username', 'leg_id', 'origin', 'destination', 'estimated_delivery_date',
        'surcharge_list', 'tracking_list', 'document_list', 'ship_date', 'markup_freight', 'markup_surcharge',
        'markup_tax', 'markup_cost', 'shipment', 'markup'
    ]
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    username = serializers.CharField(
        source="shipment.username",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    type_name = serializers.CharField(
        source="get_type_display",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Account Shipment belongs to."
    )

    carrier = serializers.CharField(
        source="carrier.name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    origin = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    surcharge_list = SurchargeSerializer(
        source='surcharge_leg.all',
        many=True,
        help_text="A list of surcharges."
    )

    tracking_list = TrackSerializer(
        source='tracking_status_leg.all',
        many=True,
        help_text="A list of documents."
    )

    document_list = DocumentSerializer(
        source='shipdocument_leg.all',
        many=True,
        help_text="A list of documents."
    )

    freight = serializers.SerializerMethodField(
        'get_marked_up_freight',
        help_text='Marked Up Freight Cost of the shipment.',
        required=False
    )

    surcharge = serializers.SerializerMethodField(
        'get_marked_up_surcharges',
        help_text='Marked Up Surcharges of the shipment.',
        required=False
    )

    tax = serializers.SerializerMethodField(
        'get_marked_up_tax',
        help_text='Marked Up Tax of the shipment.',
        required=False
    )

    cost = serializers.SerializerMethodField(
        'get_marked_up_cost',
        help_text='Marked Up Total cost of the shipment.',
        required=False
    )

    class Meta:
        model = Leg
        fields = [
            'id',
            'username',
            'leg_id',
            'type',
            'type_name',
            'carrier',
            'service_code',
            'service_name',
            'origin',
            'destination',
            'markup',
            'freight',
            'surcharge',
            'tax',
            'cost',
            'tracking_identifier',
            'carrier_pickup_identifier',
            'pickup_status',
            'pickup_message',
            'transit_days',
            'ship_date',
            'on_hold',
            'estimated_delivery_date',
            'updated_est_delivery_date',
            'delivered_date',
            'is_shipped',
            'is_dangerous_good',
            'is_shipped',
            'is_delivered',
            'surcharge_list',
            'tracking_list',
            'document_list',
            'is_pickup_overdue',
            'is_overdue'
        ]

    def get_marked_up_freight(self, obj):
        multiplier = (obj.markup / 100) + 1
        return Decimal(obj.freight * multiplier).quantize(self._price_sig_fig)

    def get_marked_up_surcharges(self, obj):
        multiplier = (obj.markup / 100) + 1
        return Decimal(obj.surcharge * multiplier).quantize(self._price_sig_fig)

    def get_marked_up_tax(self, obj):
        multiplier = (obj.markup / 100) + 1
        return Decimal(obj.tax * multiplier).quantize(self._price_sig_fig)

    def get_marked_up_cost(self, obj):
        multiplier = (obj.markup / 100) + 1
        return Decimal(obj.cost * multiplier).quantize(self._price_sig_fig)

    def update(self, instance, validated_data):
        """
            Update a port.
            :param instance:
            :param validated_data:
            :return:
        """
        statuses = []

        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        tracking = validated_data.get("tracking_identifier", "")
        pickup = validated_data.get("carrier_pickup_identifier", "")

        if tracking and tracking != instance.tracking_identifier:
            statuses.append(TrackingStatus.create(param_dict={
                "leg": instance,
                "status": "InTransit",
                "details": f"Tracking changed from {instance.tracking_identifier} to {tracking}."
            }))

        if pickup and pickup != instance.carrier_pickup_identifier:
            statuses.append(TrackingStatus.create(param_dict={
                "leg": instance,
                "status": "InTransit",
                "details": f"Pickup Number updated from {instance.carrier_pickup_identifier} to {pickup}."
            }))

        instance.set_values(pairs=validated_data)
        instance.save()

        TrackingStatus.objects.bulk_create(statuses)

        self.instance = instance
