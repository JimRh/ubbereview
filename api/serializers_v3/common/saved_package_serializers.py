"""
    Title: Saved Package Serializers
    Description: This file will contain all functions for Saved Package serializers.
    Created: October 26, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
import base64
from decimal import Decimal
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from openpyxl import load_workbook
from rest_framework import serializers

from api.apis.uploads.saved_package_upload import SavedPackageUpload
from api.exceptions.project import ViewException
from api.globals.project import API_MAX_PACK_CHAR, API_PACKAGE_TYPES, DIMENSION_PRECISION, MAX_DIMENSION_DIGITS, \
    WEIGHT_PRECISION, MAX_WEIGHT_DIGITS
from api.models import SavedPackage, SubAccount
from api.utilities.utilities import Utility


class SavedPackageSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.',
        required=True
    )

    account = serializers.CharField(
        source='sub_account.contact.company_name',
        help_text='Sub Account, account name',
        read_only=True
    )

    freight_class_id = serializers.CharField(
        help_text='NNFC Freight Class',
        max_length=API_MAX_PACK_CHAR,
        default="70.00",
        required=False
    )

    package_type = serializers.ChoiceField(
        choices=API_PACKAGE_TYPES,
        help_text="Type of package, box, skid...",
        required=False
    )

    description = serializers.CharField(
        help_text='Description of package (Be Precise)',
        max_length=API_MAX_PACK_CHAR
    )

    length = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Length of package (Individual piece)',
    )

    width = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Width of package (Individual piece)',
    )

    height = serializers.DecimalField(
        decimal_places=DIMENSION_PRECISION,
        max_digits=MAX_DIMENSION_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Height of package (Individual piece)',
    )

    weight = serializers.DecimalField(
        decimal_places=WEIGHT_PRECISION,
        max_digits=MAX_WEIGHT_DIGITS,
        min_value=Decimal("1.00"),
        help_text='Weight of package (Individual piece)',
    )

    class Meta:
        model = SavedPackage
        fields = [
            'id',
            'account_number',
            'account',
            'box_type',
            'package_type',
            'freight_class_id',
            'description',
            'width',
            'length',
            'height',
            'weight'
        ]

    def create(self, validated_data):
        """
            Create New Saved Package.
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
            raise ViewException(code="1209", message="Saved Package: Sub Account not found.", errors=errors)

        del validated_data["sub_account"]

        instance = SavedPackage.create(param_dict=validated_data)
        instance.sub_account = sub_account
        instance.save()

        return instance

    def update(self, instance, validated_data):
        """
            Update a Saved Package.
            :param instance:
            :param validated_data:
            :return:
        """

        del validated_data["sub_account"]
        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class UploadSavedPackageSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.'
    )

    file = serializers.CharField(
        help_text='Excel Rate Sheet'
    )

    class Meta:
        model = SavedPackage
        fields = [
            'account_number',
            'file',
            'box_type'
        ]

    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []

        try:
            document = base64.b64decode(validated_data["file"])
            file = BytesIO()
            file.write(document)
        except Exception:
            connection.close()
            errors.append({"document": "Document must be encoded in base64."})
            raise ViewException(code="1312", message="Document: must be encoded in base64.", errors=errors)

        wb = load_workbook(file)
        ws = wb.active

        SavedPackageUpload().import_saved_package(
            workbook=ws,
            account_number=validated_data["sub_account"],
            box_type=validated_data["box_type"]
        )

        return {"message": "Saved Package has been uploaded."}

