"""
    Title: Leg Serializers
    Description: This file will contain all functions for Leg serializers.
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_CHAR_LEN, BASE_TEN, PRICE_PRECISION, LETTER_MAPPING_LEN
from api.models import Leg, TrackingStatus, Province, Shipment, Carrier, Address
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.track_serializers import TrackSerializer
from api.serializers_v3.common.document_serializer import DocumentSerializer
from api.serializers_v3.common.surcharge_serializer import SurchargeSerializer
from django.db import connection, transaction


class PrivateLegSerializer(serializers.ModelSerializer):
    not_changeable = [
        'id', 'sub_account', 'username', 'leg_id', 'origin', 'destination', 'estimated_delivery_date',
        'surcharge_list', 'tracking_list', 'document_list', 'ship_date', 'markup_freight', 'markup_surcharge',
        'markup_tax', 'markup_cost', 'shipment', 'markup'
    ]
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    sub_account = serializers.CharField(
        source="shipment.subaccount.contact.company_name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

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

    tracking_list = serializers.SerializerMethodField(
        'get_tracking_list',
        help_text="A list of documents.",
        required=False
    )

    document_list = DocumentSerializer(
        source='shipdocument_leg.all',
        many=True,
        help_text="A list of documents."
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

    original_currency_freight = serializers.SerializerMethodField(
        'get_original_freight',
        help_text='Marked Up Freight Cost of the shipment.',
        required=False
    )

    original_currency_surcharge = serializers.SerializerMethodField(
        'get_original_surcharges',
        help_text='Marked Up Surcharges of the shipment.',
        required=False
    )

    original_currency_tax = serializers.SerializerMethodField(
        'get_original_tax',
        help_text='Marked Up Tax of the shipment.',
        required=False
    )

    original_currency_cost = serializers.SerializerMethodField(
        'get_original_cost',
        help_text='Marked Up Total cost of the shipment.',
        required=False
    )

    class Meta:
        model = Leg
        fields = [
            'id',
            'sub_account',
            'username',
            'leg_id',
            'type',
            'type_name',
            'carrier',
            'service_code',
            'service_name',
            'origin',
            'destination',
            "exchange_rate_date",
            "original_currency",
            'original_currency_freight',
            'original_currency_surcharge',
            'original_currency_tax',
            'original_currency_cost',
            "exchange_rate_original_to_base",
            "exchange_rate_base_to_original",
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
            'markup',
            'markup_freight',
            'markup_surcharge',
            'markup_tax',
            'markup_cost',
            'tracking_identifier',
            'carrier_pickup_identifier',
            'pickup_status',
            'pickup_message',
            'carrier_api_id',
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

    def get_original_freight(self, obj):
        return Decimal(obj.freight * obj.exchange_rate_base_to_original).quantize(self._price_sig_fig)

    def get_original_surcharges(self, obj):
        return Decimal(obj.surcharge * obj.exchange_rate_base_to_original).quantize(self._price_sig_fig)

    def get_original_tax(self, obj):
        return Decimal(obj.tax * obj.exchange_rate_base_to_original).quantize(self._price_sig_fig)

    def get_original_cost(self, obj):
        return Decimal(obj.cost * obj.exchange_rate_base_to_original).quantize(self._price_sig_fig)

    def get_tracking_list(self, instance):
        tracking = instance.tracking_status_leg.all().order_by('updated_datetime')
        return TrackSerializer(tracking, many=True).data

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

        instance.set_values(pairs=validated_data)
        instance.save()

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

        TrackingStatus.objects.bulk_create(statuses)

        self.instance = instance


class CreateLegSerializer(serializers.ModelSerializer):

    postfix = serializers.CharField(
        help_text="Leg Postfix, ex: 'M or P or D', but cannot be these three.",
        max_length=LETTER_MAPPING_LEN
    )

    carrier_code = serializers.IntegerField(
        source="carrier.code",
        help_text="Carrier Code"
    )

    origin = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    estimated_delivery_date = serializers.DateField(
        help_text="The estimated delivery date in format YYYY-MM-DD. (UTC)",
        format="%Y-%m-%d"
    )

    class Meta:
        model = Leg
        fields = [
            'type',
            'postfix',
            'ship_date',
            'carrier_code',
            'service_code',
            'service_name',
            'origin',
            'destination',
            'tracking_identifier',
            'carrier_pickup_identifier',
            'transit_days',
            'estimated_delivery_date',
            'freight',
            'surcharge',
            'tax',
            'cost',
            'is_dangerous_good',
        ]

    @staticmethod
    def _get_province(code: str, country: str) -> Province:
        """

            :param code:
            :param country:
            :return:
        """
        errors = []

        try:
            province = Province.objects.get(code=code, country__code=country)
        except ObjectDoesNotExist as e:
            connection.close()
            errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
            raise ViewException(code="2809", message=f'Leg: Province not found.', errors=errors)

        return province

    @transaction.atomic()
    def create(self, validated_data):
        """
            Create new leg for shipment.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            shipment = Shipment.objects.get(shipment_id=validated_data["shipment_id"])
            del validated_data["shipment_id"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"shipment": f"'shipment_id' does not exist."})
            raise ViewException(code="2807", message=f'Leg: Shipment not found.', errors=errors)

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            validated_data["carrier"] = carrier
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"carrier": f"'carrier_code' does not exist."})
            raise ViewException(code="2808", message=f'Leg: Carrier not found.', errors=errors)

        o_province = self._get_province(
            code=validated_data["origin"]["province"]["code"],
            country=validated_data["origin"]["province"]["country"]["code"]
        )

        d_province = self._get_province(
            code=validated_data["destination"]["province"]["code"],
            country=validated_data["destination"]["province"]["country"]["code"]
        )

        try:
            validated_data["origin"]["province"] = o_province
            origin = Address.create(param_dict=validated_data["origin"])
            validated_data["origin"] = origin
            origin.save()
        except ValidationError as e:
            connection.close()
            errors.append({"origin": f"'origin' failed to create: {str(e)}"})
            raise ViewException(code="2810", message='Leg: Origin address failed to create.', errors=errors)

        try:
            validated_data["destination"]["province"] = d_province
            destination = Address.create(param_dict=validated_data["destination"])
            validated_data["destination"] = destination
            destination.save()
        except ValidationError as e:
            connection.close()
            errors.append({"destination": f"'destination' failed to create: {str(e)}"})
            raise ViewException(code="2811", message='Leg: Destination address failed to create.', errors=errors)

        carrier_markup = shipment.subaccount.markup.get_carrier_percentage(carrier=carrier)

        dt = datetime.datetime.combine(validated_data["estimated_delivery_date"], datetime.datetime.min.time())

        try:
            leg = Leg.create(param_dict=validated_data)
            leg.shipment = shipment
            leg.leg_id = f"{shipment.shipment_id}{validated_data['postfix']}"
            leg.carrier = carrier
            leg.origin = origin
            leg.destination = destination
            leg.markup = carrier_markup
            leg.estimated_delivery_date = dt
            leg.save()
        except ValidationError as e:
            connection.close()
            errors.append({"leg": f"Failed to create: {str(e)}"})
            raise ViewException(code="2812", message='Leg: failed to create.', errors=errors)
        except IntegrityError:
            leg_id = f"{shipment.shipment_id}{validated_data['postfix']}"
            connection.close()
            errors.append({"leg": f"'leg_id' already exists: '{leg_id}'"})
            raise ViewException(code="2813", message="Leg: 'leg_id' already exists.", errors=errors)

        status = TrackingStatus.create(param_dict={
            "leg": leg,
            "status": "Created",
            "details": f"Shipment has been created."
        })
        status.save()

        self.instance = leg
