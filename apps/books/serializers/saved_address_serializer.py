"""
    Title: Saved Address Serializers
    Description: This file will contain all functions for Address serializers.
    Created: February 1, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import base64
import re
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from openpyxl import load_workbook
from rest_framework import serializers

from api.models import SubAccount, Province, Address
from api.serializers_v3.common.address_serializer import AddressSerializer
from apps.books.models import SavedAddress
from apps.books.uploads.saved_address_upload import SavedAddressUpload
from apps.common.globals.project import POSTAL_CODE_REGEX, POSTAL_CODE_FORMAT
from apps.common.utilities.address import (
    clean_address,
    clean_city,
    clean_postal_code,
    hash_address,
)


class SavedAddressSerializer(serializers.ModelSerializer):
    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination.",
    )

    class Meta:
        model = SavedAddress
        fields = [
            "id",
            "username",
            "name",
            "address",
            "is_origin",
            "is_destination",
            "is_vendor",
        ]

    def update(self, instance, validated_data):
        """
        Update a Saved Address.
        :param instance:
        :param validated_data:
        :return: saved address instance
        """
        errors = dict()
        del validated_data["username"]

        address = validated_data.pop("address")
        province_code = address["province"]["code"]
        country_code = address["province"]["country"]["code"]

        try:
            address["province"] = Province.objects.get(
                code=province_code, country__code=country_code
            )
        except ObjectDoesNotExist:
            errors["province"] = [
                f"Not found with 'code': {province_code} and 'country': {country_code}."
            ]

        if errors:
            connection.close()
            raise serializers.ValidationError(errors)

        instance.address.set_values(pairs=address)
        instance.address.save()

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class CreateSavedAddressSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(
        source="account.subaccount_number",
        help_text="Account number to saved address to.",
        required=True,
    )

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination.",
    )

    class Meta:
        model = SavedAddress
        fields = [
            "account_number",
            "username",
            "name",
            "address",
            "is_origin",
            "is_destination",
            "is_vendor",
        ]

    def validate(self, data):
        """

        :param data:
        :return:
        """

        errors = dict()
        address_errors = dict()

        country = data["address"]["province"]["country"]["code"]
        province = data["address"]["province"]["code"]

        postal_regex = POSTAL_CODE_REGEX.get(country, "^.*$")
        postal_format = POSTAL_CODE_FORMAT.get(country, "")

        data["address"]["address"] = clean_address(address=data["address"]["address"])
        data["address"]["city"] = clean_city(city=data["address"]["city"])
        data["address"]["postal_code"] = clean_postal_code(
            postal_code=data["address"]["postal_code"]
        )

        if not re.compile(postal_regex).fullmatch(data["address"]["postal_code"]):
            address_errors["postal_code"] = [
                f"Does not match format {postal_format} for {country}"
            ]

        if not Province.objects.filter(code=province, country__code=country).exists():
            address_errors["province"] = [
                f"Not found with 'code': {province} and 'country': {country}."
            ]

        if errors or address_errors:
            errors["address"] = address_errors
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """
        Create New Saved Address.
        :param validated_data:
        :return: Saved Address Instance
        """

        errors = {}

        account = validated_data["account"]["subaccount_number"]
        address = validated_data.pop("address")
        province = address["province"]["code"]
        country = address["province"]["country"]["code"]
        address_hash = hash_address(data=address)

        try:
            account = SubAccount.objects.get(subaccount_number=account)
        except ObjectDoesNotExist:
            errors["account"] = ["Account not found."]
            connection.close()
            raise serializers.ValidationError(errors)

        if SavedAddress.objects.filter(
            account=account, address_hash=address_hash
        ).exists() and not validated_data["is_vendor"]:
            errors["address"] = {}
            errors["address"]["address"] = [f"Saved Address already exists."]
            connection.close()
            raise serializers.ValidationError(errors)

        if validated_data["is_vendor"]:
            address_hash += f'-vendor-{validated_data["username"]}'

        validated_data["address_hash"] = address_hash
        address["province"] = Province.objects.get(code=province, country__code=country)
        address["address"] = clean_address(address=address["address"])
        address["city"] = clean_city(city=address["city"])
        address["postal_code"] = clean_postal_code(postal_code=address["postal_code"])

        address = Address.create(param_dict=address)
        address.save()

        validated_data["address"] = address
        validated_data["account"] = account

        instance = SavedAddress.create(param_dict=validated_data)
        instance.address = address
        instance.account = account
        instance.save()

        return instance


class UploadSavedAddressSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(
        source="account.subaccount_number", help_text=" Account, account number."
    )

    file = serializers.CharField(help_text="Excel of Address")

    class Meta:
        model = SavedAddress
        fields = ["account_number", "username", "file", "is_vendor"]

    def create(self, validated_data):
        """
        Upload New Saved Addresses.
        :param validated_data:
        :return: Message
        """
        errors = dict()

        try:
            document = base64.b64decode(validated_data["file"])
            file = BytesIO()
            file.write(document)
        except Exception:
            errors["file"] = ["Document: must be encoded in base64."]
            connection.close()
            raise serializers.ValidationError(errors)

        wb = load_workbook(file)
        ws = wb.active

        SavedAddressUpload().import_saved_address(workbook=ws, data=validated_data)

        connection.close()
        return {"message": "Saved Address has been uploaded."}
