"""
    Title: Private Skyline Account Serializers
    Description: This file will contain all functions for private skyline account serializers.
    Created: December 02, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import DEFAULT_CHAR_LEN
from api.models import SkylineAccount, SubAccount


class PrivateSkylineAccountSerializer(serializers.ModelSerializer):

    not_changeable = [
        'id', 'sub_account'
    ]

    account = serializers.CharField(
        source="sub_account.contact.company_name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Account Shipment belongs to.",
        required=False
    )

    account_number = serializers.CharField(
        source="sub_account.subaccount_number",
        help_text='Account id that the shipment belongs to.',
        required=False
    )

    class Meta:
        model = SkylineAccount
        fields = [
            'id',
            'account',
            'account_number',
            'skyline_account',
            'customer_id'
        ]


class PrivateCreateSkylineAccountSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source="sub_account.subaccount_number",
        help_text='Account id that the shipment belongs to.',
        required=False
    )

    class Meta:
        model = SkylineAccount
        fields = [
            'account_number',
            'skyline_account',
            'customer_id'
        ]

    def create(self, validated_data):
        """
            Create new skyline account
            :param validated_data:
            :return:
        """
        sub_account_number = validated_data["sub_account"]["subaccount_number"]

        try:
            sub_account = SubAccount.objects.get(subaccount_number=sub_account_number)
        except ObjectDoesNotExist:
            connection.close()
            errors = [{"sub_account": f"Sub account not found. '{sub_account_number}'."}]
            raise ViewException(code="5709", message=f'CN Account: Sub account not found.', errors=errors)

        skyline = SkylineAccount.create(param_dict=validated_data)
        skyline.sub_account = sub_account
        skyline.save()

        return skyline
