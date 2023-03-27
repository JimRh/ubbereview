"""
    Title: Transaction Serializers
    Description: This file will contain all functions for Transaction serializers.
    Created: June 11, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_CHAR_LEN
from api.models import Transaction, Shipment


class PrivateTransactionSerializer(serializers.ModelSerializer):
    not_changeable = [
        'id', 'shipment', 'transaction_date', 'transaction_id', 'transaction_number', 'transaction_amount',
        'auth_code', 'receipt_id'
    ]

    shipment_id = serializers.CharField(
        source="shipment.shipment_id",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Shipment Id for transaction."
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'shipment_id',
            'transaction_date',
            'payment_date',
            'payment_time',
            'transaction_id',
            'transaction_number',
            'transaction_amount',
            'transaction_type',
            'complete',
            'card_type',
            'code',
            'message',
            'auth_code',
            'iso',
            "receipt_id",
            'is_pre_authorized',
            'is_captured',
            'is_payment'
        ]

        extra_kwargs = {
            'transaction_id': {'validators': []},
        }

    @staticmethod
    def create(validated_data) -> Transaction:
        """
            Create new leg for shipment.
            :param validated_data:
            :return:
        """
        errors = []

        if Transaction.objects.filter(transaction_id=validated_data["transaction_id"]).exists():
            errors.append({"transaction_id": f"'transaction_id' already exist."})
            raise ViewException(code="X", message=f'Transaction: transaction_id already exist.', errors=errors)

        try:
            shipment = Shipment.objects.get(shipment_id=validated_data["shipment"]["shipment_id"])
            validated_data["shipment"] = shipment
        except ObjectDoesNotExist:
            errors.append({"shipment": f"'shipment_id' does not exist."})
            raise ViewException(code="X", message=f'Transaction: Shipment not found.', errors=errors)

        transaction = Transaction.create(param_dict=validated_data)
        transaction.save()

        return transaction

    def update(self, instance, validated_data):
        """
            Update City Alias for a carrier.
            :param instance:
            :param validated_data:
            :return:
        """

        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        instance.set_values(validated_data)
        instance.save()

        return instance
