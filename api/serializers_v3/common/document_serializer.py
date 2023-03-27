"""
    Title: Ship Document Serializers
    Description: This file will contain all functions for Ship Document serializers.
    Created: Jan 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
import copy
import os
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import connection, transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.globals.project import LEG_ID_LENGTH
from api.models import ShipDocument, Leg


class CreateDocumentSerializer(serializers.ModelSerializer):

    leg_id = serializers.RegexField(
        max_length=LEG_ID_LENGTH,
        min_length=LEG_ID_LENGTH,
        regex=r'^(ub)(\d{10})(\w{1})$'
    )

    document = serializers.CharField(
        help_text="Base64 encode document."
    )

    file_name = serializers.CharField(
        help_text="File Name."
    )

    class Meta:
        model = ShipDocument
        fields = [
            'leg_id',
            'new_type',
            'document',
            'file_name'
        ]

    @transaction.atomic()
    def create(self, validated_data):
        """
            Create new leg for shipment.
            :param validated_data:
            :return:
        """
        errors = []
        sub_account = validated_data["sub_account"]

        try:
            leg = Leg.objects.get(leg_id=validated_data["leg_id"])
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"leg_id": f'Leg with {validated_data["leg_id"]} not found.'})
            raise ViewException(code="1308", message="Document: 'leg_id' does not exist.", errors=errors)

        if not sub_account.is_bbe:

            if leg.shipment.subaccount != sub_account:
                errors.append({"document": "You are not allowed to add documents to another accounts leg"})
                raise ViewException(code="1309", message="Document: Invalid Permissions.", errors=errors)

            if validated_data["new_type"] not in ["0", "1", "2", "3", "4", "7"]:
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
            name=f"{leg.leg_id}-{validated_data['file_name']}"
        )

        document = ShipDocument(
            leg=leg,
            document=file,
            type=validated_data['new_type'],
            new_type=validated_data['new_type'],
        )
        document.save()
        document.document.close()

        return document


class DocumentSerializer(serializers.ModelSerializer):

    type_name = serializers.CharField(
        source="get_new_type_display",
        help_text='Document Type Name.',
        required=False
    )

    document = serializers.SerializerMethodField(
        'base_64_document',

        help_text='Base 64 document',
        required=False
    )

    file_name = serializers.SerializerMethodField(
        'get_file_name',
        help_text='Document Filename',
        required=False
    )

    class Meta:
        model = ShipDocument
        fields = [
            'id',
            'new_type',
            'type_name',
            'file_name',
            'document'
        ]

    @staticmethod
    def base_64_document(obj):
        encoded_base64 = base64.b64encode(obj.document.file.read())
        encoded_str = encoded_base64.decode('utf-8')
        return encoded_str

    @staticmethod
    def get_file_name(obj):
        return os.path.basename(obj.document.name)


class UpdateDocumentSerializer(serializers.ModelSerializer):

    document = serializers.CharField(
        help_text="Base64 encode document."
    )

    file_name = serializers.CharField(
        help_text="File Name."
    )

    class Meta:
        model = ShipDocument
        fields = [
            'document',
            'file_name'
        ]

    @transaction.atomic()
    def update(self, instance: ShipDocument, validated_data):
        """
            Update a port.
            :param instance:
            :param validated_data:
            :return:
        """

        errors = []
        leg = copy.deepcopy(instance.leg)
        doc_type = copy.deepcopy(instance.new_type)
        path = copy.deepcopy(instance.document.path)
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
            name=f"{leg.leg_id}-{validated_data['file_name']}"
        )

        document = ShipDocument(
            leg=leg,
            document=file,
            type=doc_type,
            new_type=doc_type
        )
        document.save()
        document.document.close()
        return document


class DeleteDocumentSerializer(serializers.ModelSerializer):

    leg_id = serializers.RegexField(
        max_length=LEG_ID_LENGTH,
        min_length=LEG_ID_LENGTH,
        regex=r'^(ub)(\d{10})(\w{1})$'
    )

    class Meta:
        model = ShipDocument
        fields = [
            'leg_id',
            'new_type'
        ]
