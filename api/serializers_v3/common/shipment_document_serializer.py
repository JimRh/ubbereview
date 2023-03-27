"""
    Title: Shipment Document Serializers
    Description: This file will contain all functions for Shipment Document serializers.
    Created: June 23, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
import copy
import os
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import connection, transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import ID_LENGTH
from api.models import ShipmentDocument, Shipment


class CreateShipmentDocumentSerializer(serializers.ModelSerializer):

    shipment_id = serializers.RegexField(
        max_length=ID_LENGTH,
        min_length=ID_LENGTH,
        regex=r'^(ub)(\d{10})$'
    )

    document = serializers.CharField(
        help_text="Base64 encode document."
    )

    file_name = serializers.CharField(
        help_text="File Name."
    )

    class Meta:
        model = ShipmentDocument
        fields = [
            'shipment_id',
            'type',
            'document',
            'file_name',
            'is_bbe_only'
        ]

    @transaction.atomic()
    def create(self, validated_data):
        """
            Create new shipment.
            :param validated_data:
            :return:
        """
        errors = []
        sub_account = validated_data["sub_account"]

        try:
            shipment = Shipment.objects.get(shipment_id=validated_data["shipment_id"])
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"shipment_id": f'Shipment with {validated_data["shipment_id"]} not found.'})
            raise ViewException(code="1308", message="Document: 'shipment_id' does not exist.", errors=errors)

        if not sub_account.is_bbe:
            if shipment.subaccount != sub_account:
                errors.append({"document": "You are not allowed to add documents to another account shipment"})
                raise ViewException(code="1309", message="Document: Invalid Permissions.", errors=errors)

            if validated_data["type"] not in ["0", "1", "2", "3", "5", "6", "7", "8"]:
                errors.append({"document": "You are not allowed to add this document type."})
                raise ViewException(code="1309", message="Document: Invalid Permissions.", errors=errors)

        try:
            document = base64.b64decode(validated_data["document"])
        except Exception:
            connection.close()
            errors.append({"document": "Document must be encoded in base64."})
            raise ViewException(code="1311", message="Document: must be encoded in base64.", errors=errors)

        file = BytesIO()
        file.write(document)

        file = File(
            file,
            name=f"{shipment.shipment_id}-{validated_data['file_name']}"
        )

        document = ShipmentDocument(
            shipment=shipment,
            document=file,
            type=validated_data['type']
        )
        document.save()
        document.document.close()

        return document


class ShipmentDocumentSerializer(serializers.ModelSerializer):

    type_name = serializers.CharField(
        source="get_type_display",
        help_text='Document Type Name.',
    )

    file_name = serializers.SerializerMethodField(
        'get_file_name',
        help_text='Document Filename',
        required=False
    )

    document = serializers.SerializerMethodField(
        'base_64_document',
        help_text='Base 64 document',
        required=False
    )

    class Meta:
        model = ShipmentDocument
        fields = [
            'id',
            'type',
            'type_name',
            'file_name',
            'document',
            'is_bbe_only'
        ]

    @staticmethod
    def base_64_document(obj):
        encoded_base64 = base64.b64encode(obj.document.file.read())
        encoded_str = encoded_base64.decode('utf-8')
        return encoded_str

    @staticmethod
    def get_file_name(obj):
        return os.path.basename(obj.document.name)


class UpdateShipmentDocumentSerializer(serializers.ModelSerializer):

    document = serializers.CharField(
        help_text="Base64 encode document."
    )

    file_name = serializers.CharField(
        help_text="File Name."
    )

    class Meta:
        model = ShipmentDocument
        fields = [
            'document',
            'file_name',
        ]

    @transaction.atomic()
    def update(self, instance: ShipmentDocument, validated_data):
        """
            Update a port.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []
        shipment = copy.deepcopy(instance.shipment)
        path = copy.deepcopy(instance.document.path)
        doc_type = copy.deepcopy(instance.type)
        instance.delete()
        default_storage.delete(path)

        try:
            document = base64.b64decode(validated_data["document"])
        except Exception:
            connection.close()
            errors.append({"document": "Document must be encoded in base64."})
            raise ViewException(code="1312", message="Document: must be encoded in base64.", errors=errors)

        file = BytesIO()
        file.write(document)

        file = File(
            file,
            name=f"{shipment.shipment_id}-{validated_data['file_name']}"
        )

        document = ShipmentDocument(
            shipment=shipment,
            document=file,
            type=doc_type,
        )
        document.save()
        document.document.close()

        return document
