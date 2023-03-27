"""
    Title: Promo Code Serializers
    Description: This file will contain all functions for Saved Broker serializers.
    Created: June 08, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.globals.project import DEFAULT_CHAR_LEN, PRICE_PRECISION, MAX_PRICE_DIGITS
from api.models import PromoCode


class PromoCodeSerializer(serializers.ModelSerializer):

    code = serializers.CharField(
        required=False,
        help_text="Promo Code"
    )
    is_bulk = serializers.BooleanField(
        required=False,
        help_text="Promo Code"
    )
    amount = serializers.IntegerField(
        required=False,
        help_text="Promo Code"
    )

    class Meta:
        model = PromoCode
        fields = [
            'id',
            'code',
            'start_date',
            'end_date',
            'quantity',
            'flat_amount',
            'min_shipment_cost',
            'max_discount',
            'percentage',
            'is_active',
            'is_bulk',
            'amount'
        ]

        extra_kwargs = {
            'code': {'validators': []},
        }


class PromoCodeBulkSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(
        help_text="Amount of promo codes to create."
    )

    class Meta:
        model = PromoCode
        fields = [
            'start_date',
            'end_date',
            'quantity',
            'flat_amount',
            'min_shipment_cost',
            'max_discount',
            'percentage',
            'is_active',
            'is_bulk',
            'amount'
        ]


class PromoCodeValidateSerializer(serializers.Serializer):

    promo_code = serializers.CharField(
        help_text="Promo Code value.",
        max_length=DEFAULT_CHAR_LEN
    )

    pre_tax_cost = serializers.DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="Pre tax shipment cost."
    )


class PromoCodeValidateResponseSerializer(serializers.Serializer):

    promo_code = serializers.CharField(
        help_text="Promo Code value.",
        max_length=DEFAULT_CHAR_LEN
    )

    discount = serializers.DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="Discount Amount"
    )

    is_valid = serializers.BooleanField(
        required=False,
        help_text="Is the promo code valid."
    )
