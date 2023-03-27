"""
    Title: Private Ship Serializers
    Description: This file will contain all functions for private ship serializers.
    Created: March 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from rest_framework import serializers

from api.globals.project import API_ZERO, API_CHAR_LEN, API_MAX_CHAR_LEN, PRICE_PRECISION, MAX_INSURANCE_DIGITS, \
    NO_INSURANCE, DEFAULT_CHAR_LEN, BASE_TEN
from api.models import Package, Leg, Shipment
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.contact_serializer import ContactSerializer
from api.serializers_v3.common.document_serializer import DocumentSerializer
from api.serializers_v3.common.ship.address_serializer import ShipAddressSerializer
from api.serializers_v3.common.ship.service_serializer import ServiceSerializer
from api.serializers_v3.private.ship.bc_serializer import ShipBCSerializer
from api.serializers_v3.public.pickup_request_serializer import PickupRequestSerializer
from api.serializers_v3.public.ship_commodity_serializers import ShipPackageCommoditySerializer
from api.serializers_v3.public.ship_package_serializer import ShipPackageSerializer


class PrivateShipRequestSerializer(serializers.Serializer):

    account_number = serializers.CharField(
        help_text='Account Number that the shipment belongs to.',
        required=False,
        allow_blank=True
    )

    service = ServiceSerializer(
        help_text="Carrier and Service information."
    )

    origin = ShipAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = ShipAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    broker = ShipAddressSerializer(
        many=False,
        help_text="A dictionary containing information about the broker.",
        required=False
    )

    packages = ShipPackageSerializer(
        many=True,
        help_text="A list containing information about the packages."
    )

    # International Only
    commodities = ShipPackageCommoditySerializer(
        many=True,
        help_text="A list containing commodities in a packages. Sum of Weight must equal package weight.",
        allow_empty=True,
        default=[]
    )

    pickup = PickupRequestSerializer(
        many=False,
        help_text="A dictionary containing information about the pickup date and time.",
        required=False
    )

    carrier_options = serializers.ListField(
        child=serializers.IntegerField(min_value=API_ZERO),
        allow_empty=True,
        help_text='List of options to include in the rate request.',
        default=[]
    )

    special_instructions = serializers.CharField(
        help_text='Any additional handling or special instructions for the carrier.',
        max_length=API_MAX_CHAR_LEN,
        default="",
        allow_blank=True
    )

    reference_one = serializers.CharField(
        help_text='Reference One (Most likely to be place on documents)',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    reference_two = serializers.CharField(
        help_text='Reference Two',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    username = serializers.CharField(
        help_text='Reference Two',
        max_length=API_MAX_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    email = serializers.CharField(
        help_text='Reference Two',
        max_length=API_MAX_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    project = serializers.CharField(
        help_text='Project Reference',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    quote_id = serializers.CharField(
        help_text='quote_id Reference',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    bc_customer_code = serializers.CharField(
        help_text='BC Customer Code',
        max_length=API_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    bc_customer_name = serializers.CharField(
        help_text='BC Customer Name',
        max_length=API_MAX_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    insurance_amount = serializers.DecimalField(
        help_text='Any value greater than 0 (zero) indicates the shipment has insurance and how much, otherwise the '
                  'shipment has no insurance. (Value of Goods)',
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_INSURANCE_DIGITS,
        default=NO_INSURANCE,
        required=False,
    )

    promo_code = serializers.CharField(
        help_text='Promo Code',
        max_length=API_MAX_CHAR_LEN,
        required=False,
        allow_blank=True
    )

    is_dangerous_goods = serializers.BooleanField(
        help_text='Is the shipment contain dangerous goods?',
        default=False
    )

    is_metric = serializers.BooleanField(
        help_text='Is the shipment in metric units (cm and kg)?',
        default=True
    )

    is_food = serializers.BooleanField(
        help_text='Does the shipment contain food?',
        default=False
    )

    is_pickup = serializers.BooleanField(
        help_text='Do you want the  shipment to be picked up?',
        default=True
    )

    bc_fields = ShipBCSerializer(
        many=False,
        help_text="A dictionary containing business central configuration details.",
        required=False
    )


class ShipResponsePackageSerializer(serializers.ModelSerializer):

    package_type_name = serializers.CharField(
        source="get_package_type_display",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Account Shipment belongs to."
    )

    class Meta:
        model = Package
        fields = [
            'id',
            'package_id',
            'package_account_id',
            'quantity',
            'width',
            'length',
            'height',
            'weight',
            'package_type',
            'package_type_name',
            'description',
            "freight_class_id",
            'un_number',
            'packing_group',
            'packing_type',
            'dg_proper_name',
            'dg_quantity',
            'dg_nos_description',
            'container_number',
            'container_pack',
            'vehicle_condition',
            'anti_theft',
            'year',
            'make',
            'vin',
        ]


class ShipResponseLegSerializer(serializers.ModelSerializer):

    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

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
            'leg_id',
            'type',
            'type_name',
            'carrier',
            'service_code',
            'service_name',
            'origin',
            'destination',
            "base_currency",
            'base_freight',
            'base_surcharge',
            'base_tax',
            'base_cost',
            'currency',
            'exchange_rate_from_base',
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


class PrivateShipResponseSerializer(serializers.ModelSerializer):

    origin = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    billing = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the billing."
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

    payer = ContactSerializer(
        source="receiver",
        many=False,
        help_text="A dictionary containing information about the payer."
    )

    packages = ShipResponsePackageSerializer(
        source='package_shipment.all',
        many=True,
        help_text="A list containing information about the packages."
    )

    legs = ShipResponseLegSerializer(
        source='leg_shipment.all',
        many=True,
        help_text="A list containing information about the packages."
    )

    class Meta:
        model = Shipment
        fields = [
            'id',
            'creation_date',
            'shipment_id',
            'account_id',
            'ff_number',
            'origin',
            'destination',
            'billing',
            'shipper',
            'consignee',
            'payer',
            'packages',
            'legs',
            'reference_one',
            'reference_two',
            'project',
            'booking_number',
            'quote_id',
            'special_instructions',
            'requested_pickup_time',
            'requested_pickup_close_time',
            'insurance_amount',
            'insurance_cost',
            'promo_code',
            'promo_code_discount',
            'is_food',
            'is_dangerous_good',
            'is_shipped',
            'is_delivered',
            'is_cancel',
            'is_cancel_completed'
        ]
