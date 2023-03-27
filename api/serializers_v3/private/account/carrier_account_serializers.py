"""
    Title: Carrier Account Serializers
    Description: This file will contain all functions for Carrier Account serializers.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import CarrierAccount, EncryptedMessage, SubAccount, Carrier


class PrivateCarrierAccountSerializer(serializers.ModelSerializer):

    account = serializers.CharField(
        source='subaccount.contact.company_name',
        help_text='Carrier Name',
        read_only=True
    )

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Name',
        read_only=True
    )

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier code'
    )

    api_key = serializers.SerializerMethodField(
        'get_api_key',
        help_text='Api Key of the carrier api.',
        required=False
    )

    username = serializers.SerializerMethodField(
        'get_username',
        help_text='Username of the carrier api.',
        required=False
    )

    password = serializers.SerializerMethodField(
        'get_password',
        help_text='Password of the carrier api.',
        required=False
    )
    account_number = serializers.SerializerMethodField(
        'get_account_number',
        help_text='Account Number of the carrier api.',
        required=False
    )

    contract_number = serializers.SerializerMethodField(
        'get_contract_number',
        help_text='Contract Number of the carrier api.',
        required=False
    )

    class Meta:
        model = CarrierAccount
        fields = [
            'id',
            'account',
            'carrier_name',
            'carrier_code',
            'api_key',
            'username',
            'password',
            'account_number',
            'contract_number'
        ]

    @staticmethod
    def get_api_key(obj):
        if not obj.api_key:
            return ""
        return obj.api_key.decrypt()

    @staticmethod
    def get_username(obj):
        if not obj.username:
            return ""
        return obj.username.decrypt()

    @staticmethod
    def get_password(obj):
        if not obj.password:
            return ""
        return obj.password.decrypt()

    @staticmethod
    def get_account_number(obj):
        if not obj.account_number:
            return ""
        return obj.account_number.decrypt()

    @staticmethod
    def get_contract_number(obj):
        if not obj.contract_number:
            return ""
        return obj.contract_number.decrypt()


class PrivateUpdateCarrierAccountSerializer(serializers.ModelSerializer):

    api_key = serializers.CharField(
        help_text='Api Key of the carrier api.',
        required=False
    )

    username = serializers.CharField(
        help_text='Username of the carrier api.',
        required=False
    )

    password = serializers.CharField(
        help_text='Password of the carrier api.',
        required=False
    )
    account_number = serializers.CharField(
        help_text='Account Number of the carrier api.',
        required=False
    )

    contract_number = serializers.CharField(
        help_text='Contract Number of the carrier api.',
        required=False
    )

    class Meta:
        model = CarrierAccount
        fields = [
            'api_key',
            'username',
            'password',
            'account_number',
            'contract_number'
        ]

    @staticmethod
    def create_encrypted_message(value: str):

        encrypted = EncryptedMessage.encrypt_message(message=value)
        encrypted.save()
        return encrypted

    @transaction.atomic
    def update(self, instance, validated_data):
        """
            Update carrier account.
            :param instance:
            :param validated_data:
            :return:
        """

        if validated_data.get("api_key"):
            old_api_key = instance.api_key
            instance.api_key = self.create_encrypted_message(value=validated_data["api_key"])

            if old_api_key:
                old_api_key.delete()

        if validated_data.get("username"):
            old_username = instance.username
            instance.username = self.create_encrypted_message(value=validated_data["username"])

            if old_username:
                old_username.delete()

        if validated_data.get("password"):
            old_password = instance.password
            instance.password = self.create_encrypted_message(value=validated_data["password"])

            if old_password:
                old_password.delete()

        if validated_data.get("account_number"):
            old_account_number = instance.account_number
            instance.account_number = self.create_encrypted_message(value=validated_data["account_number"])

            if old_account_number:
                old_account_number.delete()

        if validated_data.get("contract_number"):
            old_contract_number = instance.contract_number
            instance.contract_number = self.create_encrypted_message(value=validated_data["contract_number"])

            if old_contract_number:
                old_contract_number.delete()

        instance.save()

        return instance


class PrivateCreateCarrierAccountSerializer(serializers.ModelSerializer):

    account = serializers.CharField(
        source='subaccount.subaccount_number',
        help_text='Carrier Name'
    )

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier code'
    )

    api_key = serializers.CharField(
        help_text='Api Key of the carrier api.',
        required=False
    )

    username = serializers.CharField(
        help_text='Username of the carrier api.',
        required=False
    )

    password = serializers.CharField(
        help_text='Password of the carrier api.',
        required=False
    )
    account_number = serializers.CharField(
        help_text='Account Number of the carrier api.',
        required=False
    )

    contract_number = serializers.CharField(
        help_text='Contract Number of the carrier api.',
        required=False
    )

    class Meta:
        model = CarrierAccount
        fields = [
            'id',
            'account',
            'carrier_code',
            'api_key',
            'username',
            'password',
            'account_number',
            'contract_number'
        ]

    @staticmethod
    def create_encrypted_message(value: str):

        encrypted = EncryptedMessage.encrypt_message(message=value)
        encrypted.save()
        return encrypted

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []
        sub_account_number = validated_data["subaccount"]["subaccount_number"]
        carrier_code = validated_data["carrier"]["code"]

        exists = CarrierAccount.objects.filter(
            subaccount__subaccount_number=sub_account_number, carrier__code=carrier_code
        ).exists()

        if exists:
            errors.append({"carrier": f"Carrier account already exists for {carrier_code} and {sub_account_number}."})
            raise ViewException(code="3608", message=f'CarrierAccount: Already Exists.', errors=errors)

        carrier_account = CarrierAccount.create()

        try:
            carrier_account.subaccount = SubAccount.objects.get(subaccount_number=sub_account_number)
        except ObjectDoesNotExist:
            errors.append({"sub_account": f"Sub Account Not found."})
            raise ViewException(code="3609", message=f'CarrierAccount: Sub account not found.', errors=errors)

        try:
            carrier_account.carrier = Carrier.objects.get(code=carrier_code)
        except ObjectDoesNotExist:
            errors.append({"carrier": f"Carrier Not found for {carrier_code}"})
            raise ViewException(code="3610", message=f"CarrierAccount: Carrier not found.", errors=errors)

        if validated_data["api_key"]:
            carrier_account.api_key = self.create_encrypted_message(value=validated_data["api_key"])

        if validated_data["username"]:
            carrier_account.username = self.create_encrypted_message(value=validated_data["username"])

        if validated_data["password"]:
            carrier_account.password = self.create_encrypted_message(value=validated_data["password"])

        if validated_data["account_number"]:
            carrier_account.account_number = self.create_encrypted_message(value=validated_data["account_number"])

        if validated_data["contract_number"]:
            carrier_account.contract_number = self.create_encrypted_message(value=validated_data["contract_number"])

        carrier_account.save()

        return carrier_account
