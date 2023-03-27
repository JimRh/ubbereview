"""
    Title: Saved Contact Serializers
    Description: This file will contain all functions for Contact serializers.
    Created: February 9, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import base64
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from openpyxl import load_workbook
from rest_framework import serializers

from api.models import SubAccount, Contact
from api.serializers_v3.common.contact_serializer import ContactSerializer
from apps.books.models import SavedContact
from apps.books.uploads.saved_contact_upload import SavedContactUpload
from apps.common.utilities.contact import hash_contact


class SavedContactSerializer(serializers.ModelSerializer):

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the contact.",
    )

    class Meta:
        model = SavedContact
        fields = [
            "id",
            "username",
            "contact",
            "is_origin",
            "is_destination",
            "is_vendor",
        ]

    def update(self, instance, validated_data):
        """
        Update a Saved Contact.
        :param instance:
        :param validated_data:
        :return: saved contact instance
        """
        del validated_data["username"]

        contact = validated_data.pop("contact")

        instance.contact.set_values(pairs=contact)
        instance.contact.save()
        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class CreateSavedContactSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(
        source="account.subaccount_number",
        help_text="Account number to saved contact to.",
        required=True,
    )

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the contact.",
    )

    class Meta:
        model = SavedContact
        fields = [
            "account_number",
            "username",
            "contact",
            "is_origin",
            "is_destination",
            "is_vendor",
        ]

    def create(self, validated_data):
        """
        Create New Saved Contact.
        :param validated_data:
        :return: Saved Contact Instance
        """

        errors = {}

        account = validated_data["account"]["subaccount_number"]
        contact = validated_data.pop("contact")
        contact_hash = hash_contact(data=contact)

        try:
            account = SubAccount.objects.get(subaccount_number=account)
        except ObjectDoesNotExist:
            errors["account"] = ["Account not found."]
            connection.close()
            raise serializers.ValidationError(errors)

        if SavedContact.objects.filter(
            account=account, contact_hash=contact_hash
        ).exists() and not validated_data["is_vendor"]:
            errors["contact"] = {}
            errors["contact"]["name"] = [f"Saved Contact already exists."]
            connection.close()
            raise serializers.ValidationError(errors)

        if validated_data["is_vendor"]:
            contact_hash += f'-vendor-{validated_data["username"]}'

        contact = Contact.create(param_dict=contact)
        contact.save()

        validated_data["contact_hash"] = contact_hash
        validated_data["contact"] = contact
        validated_data["account"] = account

        instance = SavedContact.create(param_dict=validated_data)
        instance.contact = contact
        instance.account = account
        instance.save()

        return instance


class UploadSavedContactSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(
        source="account.subaccount_number", help_text=" Account, account number."
    )

    file = serializers.CharField(help_text="Excel of Contacts")

    class Meta:
        model = SavedContact
        fields = ["account_number", "username", "file", "is_vendor"]

    def create(self, validated_data):
        """
        Upload New Saved Contacts.
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

        SavedContactUpload().import_saved_contact(workbook=ws, data=validated_data)

        connection.close()
        return {"message": "Saved Contact has been uploaded."}
