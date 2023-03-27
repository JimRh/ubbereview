"""
    Title: Shipment Serializers
    Description: This file will contain all functions for shipment serializers.
    Created: December 29, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import BASE_TEN, PRICE_PRECISION
from api.models import Shipment
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.contact_serializer import ContactSerializer
from api.serializers_v3.common.shipment_document_serializer import ShipmentDocumentSerializer


class PublicShipmentSerializer(serializers.ModelSerializer):
    """
        Public Shipment Serializer for ubbe clients.
    """
    not_changeable = [
        'id', 'user', 'account', 'account_number', 'creation_date', 'shipment_id', 'origin', 'destination',
        'shipper', 'consignee', 'markup_freight', 'markup_surcharge', 'markup_tax', 'markup_cost', 'markup'
    ]
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    origin = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    shipper = ContactSerializer(
        source="sender",
        many=False,
        help_text="A dictionary containing information about the shipper."
    )

    consignee = ContactSerializer(
        source="receiver",
        many=False,
        help_text="A dictionary containing information about the consignee."
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

    document_list = ShipmentDocumentSerializer(
        source='shipment_document_shipment.all',
        many=True,
        help_text="A list of documents."
    )

    class Meta:
        model = Shipment
        fields = [
            'id',
            'creation_date',
            'username',
            'shipment_id',
            'ff_number',
            'quote_id',
            'origin',
            'destination',
            'shipper',
            'consignee',
            'freight',
            'surcharge',
            'tax',
            'cost',
            'reference_one',
            'reference_two',
            'project',
            'booking_number',
            'quote_id',
            'special_instructions',
            'requested_pickup_time',
            'requested_pickup_close_time',
            'is_food',
            'is_dangerous_good',
            'is_shipped',
            'is_delivered',
            'is_cancel',
            'is_cancel_completed',
            'document_list'
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
        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        instance.set_values(pairs=validated_data)
        instance.save()

        self.instance = instance
