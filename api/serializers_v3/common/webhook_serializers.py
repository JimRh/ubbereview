"""
    Title: Webhook Serializers
    Description: This file will contain all functions for Webhook serializers.
    Created: July 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Webhook, SubAccount


class WebhookSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.',
        required=True
    )

    account_name = serializers.CharField(
        source='sub_account.contact.company_name',
        help_text='Sub Account, account Name.',
        required=False,
        read_only=True
    )

    event_name = serializers.CharField(
        source='get_event_display',
        help_text='Event Name',
        required=False,
        read_only=True
    )

    data_name = serializers.CharField(
        source='get_data_format_display',
        help_text='Data Format Name',
        required=False,
        read_only=True
    )

    class Meta:
        model = Webhook
        fields = [
            'id',
            'account_number',
            'account_name',
            'event',
            'event_name',
            'url',
            'data_format',
            'data_name'
        ]

    def create(self, validated_data):
        """
            Create New Webhook.
            :param validated_data:
            :return:
        """
        errors = []
        account = validated_data["sub_account"]["subaccount_number"]

        try:
            sub_account = SubAccount.objects.get(subaccount_number=account)
        except ObjectDoesNotExist as e:
            connection.close()
            errors.append({"sub_account": "Sub Account not found."})
            raise ViewException(code="1209", message="Webhook: Sub Account not found.", errors=errors)

        if Webhook.objects.filter(event=validated_data["event"], sub_account__subaccount_number=account).exists():
            errors.append({"sub_account": "Sub Account already has event configured."})
            raise ViewException(code="1210", message="Webhook: Sub Account Already configured.", errors=errors)

        del validated_data["sub_account"]

        instance = Webhook.create(param_dict=validated_data)
        instance.sub_account = sub_account
        instance.save()

        return instance

    def update(self, instance, validated_data):
        """
            Update a Webhook.
            :param instance:
            :param validated_data:
            :return:
        """

        del validated_data["sub_account"]
        instance.set_values(pairs=validated_data)
        instance.save()

        return instance



