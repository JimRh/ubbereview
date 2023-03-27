"""
    Title: Private Shipment Serializers
    Description: This file will contain all functions for shipment serializers.
    Created: December 29, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import BASE_TEN, PRICE_PRECISION, DEFAULT_CHAR_LEN
from api.models import Shipment, SubAccount, Address, Contact
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.contact_serializer import ContactSerializer
from api.serializers_v3.common.shipment_document_serializer import ShipmentDocumentSerializer
from django.db import connection


class PrivateShipmentSerializer(serializers.ModelSerializer):
    """
        Private Shipment Serializer for BBE Only.
    """
    not_changeable = [
        'id', 'user', 'account', 'account_number', 'creation_date', 'shipment_id', 'origin', 'destination',
        'shipper', 'consignee', 'markup_freight', 'markup_surcharge', 'markup_tax', 'markup_cost', 'markup'
    ]
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    user = serializers.CharField(
        source="user.username",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Shipment owner."
    )

    account = serializers.CharField(
        source="subaccount.contact.company_name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Account Shipment belongs to."
    )

    account_number = serializers.CharField(
        source="subaccount.subaccount_number",
        help_text='Account id that the shipment belongs to.'
    )

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

    markup_freight = serializers.SerializerMethodField(
        'get_marked_up_freight',
        help_text='Marked Up Freight Cost of the shipment.',
        required=False
    )

    markup_surcharge = serializers.SerializerMethodField(
        'get_marked_up_surcharges',
        help_text='Marked Up Surcharges of the shipment.',
        required=False
    )

    markup_tax = serializers.SerializerMethodField(
        'get_marked_up_tax',
        help_text='Marked Up Tax of the shipment.',
        required=False
    )

    markup_cost = serializers.SerializerMethodField(
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
            'user',
            'username',
            'account',
            'account_number',
            'creation_date',
            'shipment_id',
            'ff_number',
            'quote_id',
            'origin',
            'destination',
            'shipper',
            'consignee',
            'base_currency',
            'base_freight',
            'base_surcharge',
            'base_tax',
            'base_cost',
            'currency',
            'freight',
            'surcharge',
            'tax',
            'cost',
            'markup_freight',
            'markup_surcharge',
            'markup_tax',
            'markup_cost',
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


class CreateShipmentSerializer(serializers.ModelSerializer):
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    account_number = serializers.CharField(
        source="subaccount.subaccount_number",
        help_text='Account id that the shipment belongs to.'
    )

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

    class Meta:
        model = Shipment
        fields = [
            'account_number',
            'ff_number',
            'origin',
            'destination',
            'shipper',
            'consignee',
            'freight',
            'surcharge',
            'tax',
            'cost',
            'project',
            'reference_one',
            'reference_two',
            'booking_number',
            'special_instructions',
            'username',
            'email',
            'requested_pickup_time',
            'requested_pickup_close_time',
            'is_food',
            'is_dangerous_good',
        ]

    def create(self, validated_data):
        """
            Create New Shipment.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            validated_data["subaccount"] = SubAccount.objects.get(subaccount_number=validated_data["subaccount"]["subaccount_number"])
        except ObjectDoesNotExist as e:
            connection.close()
            errors.append({"sub_account": "Sub Account not found."})
            raise ViewException(code="1209", message="Shipment: Sub Account not found.", errors=errors)

        validated_data["origin"]["country"] = validated_data["origin"]["province"]["country"]["code"]
        # prov = validated_data["origin"]["province"]["code"]
        validated_data["origin"]["province"] = validated_data["origin"]["province"]["code"]

        validated_data["destination"]["country"] = validated_data["destination"]["province"]["country"]["code"]
        # prov = validated_data["origin"]["province"]["code"]
        validated_data["destination"]["province"] = validated_data["destination"]["province"]["code"]

        validated_data["origin"] = Address.create_or_find(validated_data["origin"])
        validated_data["destination"] = Address.create_or_find(validated_data["destination"])
        validated_data["sender"] = Contact.create_or_find(validated_data["sender"])
        validated_data["receiver"] = Contact.create_or_find(validated_data["receiver"])

        instance = Shipment.create(param_dict=validated_data)
        instance.user = validated_data["user"]
        instance.subaccount = validated_data["subaccount"]
        instance.origin = validated_data["origin"]
        instance.destination = validated_data["destination"]
        instance.sender = validated_data["sender"]
        instance.receiver = validated_data["receiver"]
        instance.markup = Decimal("0.00")
        instance.save()

        return instance
