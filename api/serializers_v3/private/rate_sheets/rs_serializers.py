"""
    Title: Rate Sheet Serializers
    Description: This file will contain all functions for rate sheet serializers.
    Created: November 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import base64
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from openpyxl import load_workbook
from rest_framework import serializers

from api.apis.carriers.rate_sheets.endpoints.rs_management_v2 import NewRateSheetManagement
from api.exceptions.project import ViewException
from api.globals.project import PROVINCE_CODE_LEN, COUNTRY_CODE_LEN
from api.models import RateSheet, SubAccount, Province, Carrier


class RateSheetSerializer(serializers.ModelSerializer):
    not_changeable = [
        'sub_account', 'carrier'
    ]

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.',
        required=True
    )

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Type Name',
        required=False
    )

    carrier_code = serializers.CharField(
        source='carrier.code',
        help_text='Carrier Type Name',
        required=False
    )

    carrier_mode = serializers.CharField(
        source='carrier.get_mode_display',
        help_text='Carrier Mode Name',
        required=False
    )

    origin_province = serializers.CharField(
        source="origin_province.code",
        max_length=PROVINCE_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    origin_country = serializers.CharField(
        source="origin_province.country.code",
        max_length=COUNTRY_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    destination_province = serializers.CharField(
        source="destination_province.code",
        max_length=PROVINCE_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    destination_country = serializers.CharField(
        source="destination_province.country.code",
        max_length=COUNTRY_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    rs_type_name = serializers.CharField(
        source='get_rs_type_display',
        help_text='Carrier Type Name',
        required=False
    )

    class Meta:
        model = RateSheet
        fields = [
            'id',
            'expiry_date',
            'account_number',
            'carrier_name',
            'carrier_code',
            'carrier_mode',
            'origin_province',
            'origin_country',
            'destination_province',
            'destination_country',
            'origin_city',
            'destination_city',
            'minimum_charge',
            'maximum_charge',
            'cut_off_time',
            'transit_days',
            'service_code',
            'service_name',
            'availability',
            'rs_type_name',
            'rs_type',
        ]

    def update(self, instance, validated_data):
        """
            Update bill of lading.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []

        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        o_province = validated_data["origin_province"]
        o_country = validated_data["origin_province"]["country"]
        try:
            origin_province = Province.objects.get(code=o_province["code"], country__code=o_country["code"])
            del validated_data["origin_province"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f'Not found: \'{o_province["code"]}\' and country: \'{o_country["code"]}\'.'})
            raise ViewException(code="6216", message=f'RateSheet: Origin province not found.', errors=errors)

        d_province = validated_data["destination_province"]
        d_country = validated_data["destination_province"]["country"]
        try:
            destination_province = Province.objects.get(code=d_province["code"], country__code=d_country["code"])
            del validated_data["destination_province"]
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f'Not found: \'{d_province["code"]}\' and country: \'{d_country["code"]}\'.'})
            raise ViewException(code="6217", message=f'RateSheet: Destination province not found.', errors=errors)

        validated_data["origin_city"] = validated_data["origin_city"].strip().title()
        validated_data["destination_city"] = validated_data["destination_city"].strip().title()

        instance.set_values(pairs=validated_data)
        instance.origin_province = origin_province
        instance.destination_province = destination_province
        instance.save()

        return instance


class CreateRateSheetSerializer(serializers.ModelSerializer):

    expiry_date = serializers.CharField(
        help_text='The date the lane Expires',
        required=True
    )

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.',
        required=True
    )

    carrier_code = serializers.CharField(
        source='carrier.code',
        help_text='Carrier Type Name',
        required=True
    )

    origin_province = serializers.CharField(
        source="origin_province.code",
        max_length=PROVINCE_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    origin_country = serializers.CharField(
        source="origin_province.country.code",
        max_length=COUNTRY_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    destination_province = serializers.CharField(
        source="destination_province.code",
        max_length=PROVINCE_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    destination_country = serializers.CharField(
        source="destination_province.country.code",
        max_length=COUNTRY_CODE_LEN,
        help_text='Province code. Ex: AB.',
        required=True
    )

    class Meta:
        model = RateSheet
        fields = [
            'id',
            'account_number',
            'expiry_date',
            'carrier_code',
            'origin_city',
            'origin_province',
            'origin_country',
            'destination_city',
            'destination_province',
            'destination_country',
            'minimum_charge',
            'maximum_charge',
            'cut_off_time',
            'transit_days',
            'service_code',
            'service_name',
            'availability',
            'rs_type'
        ]

    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []
        sub_account_number = validated_data["sub_account"]["subaccount_number"]

        try:
            sub_account = SubAccount.objects.get(subaccount_number=sub_account_number)
            validated_data["sub_account"] = sub_account
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"sub_account": f"Sub account not found. '{sub_account_number}'."})
            raise ViewException(code="6211", message=f'RateSheet: Sub account not found.', errors=errors)

        carrier_code = validated_data["carrier"]["code"]
        try:
            carrier = Carrier.objects.get(code=carrier_code)
            validated_data["carrier"] = carrier
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"carrier": f"Carrier with carrier code '{carrier_code}' not found"})
            raise ViewException(code="6212", message=f'RateSheet: Carrier not found.', errors=errors)

        o_province = validated_data["origin_province"]
        o_country = validated_data["origin_province"]["country"]
        try:
            origin_province = Province.objects.get(code=o_province["code"], country__code=o_country["code"])
            validated_data["origin_province"] = origin_province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f'Not found: \'{o_province["code"]}\' and country: \'{o_country["code"]}\'.'})
            raise ViewException(code="6213", message=f'RateSheet: Origin province not found.', errors=errors)

        d_province = validated_data["destination_province"]
        d_country = validated_data["destination_province"]["country"]
        try:
            destination_province = Province.objects.get(code=d_province["code"], country__code=d_country["code"])
            validated_data["destination_province"] = destination_province
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"province": f'Not found: \'{d_province["code"]}\' and country: \'{d_country["code"]}\'.'})
            raise ViewException(code="6214", message=f'RateSheet: Destination province not found.', errors=errors)

        validated_data["origin_city"] = validated_data["origin_city"].strip().title()
        validated_data["destination_city"] = validated_data["destination_city"].strip().title()
        origin_city = validated_data["origin_city"]
        destination_city = validated_data["destination_city"]

        exists = RateSheet.objects.filter(
            sub_account=sub_account,
            carrier=carrier,
            service_code=validated_data["service_code"],
            origin_city=origin_city,
            origin_province=origin_province,
            destination_city=destination_city,
            destination_province=destination_province
        ).exists()

        if exists:
            errors.append({"rate_sheet": f'Lane already exists for {origin_city} to {destination_city}.'})
            raise ViewException(code="6215", message=f'RateSheet: Lane already exists.', errors=errors)

        rate_sheet = RateSheet.create(param_dict=validated_data)
        rate_sheet.save()

        return rate_sheet


class DeleteRateSheetSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.',
        required=True
    )

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Type Name',
        required=True
    )

    class Meta:
        model = RateSheet
        fields = [
            'id',
            'account_number',
            'carrier_code',
            'service_code',
        ]


class UploadRateSheetSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.'
    )

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Type Name'
    )

    service_name = serializers.CharField(
        help_text='Carrier Type Name'
    )

    file = serializers.CharField(
        help_text='Excel Rate Sheet'
    )

    class Meta:
        model = RateSheet
        fields = [
            'account_number',
            'rs_type',
            'carrier_code',
            'service_name',
            'service_code',
            'file'
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
        sub_account = validated_data["sub_account"]["subaccount_number"]
        carrier_code = validated_data["carrier"]["code"]

        try:
            sub_account = SubAccount.objects.get(subaccount_number=sub_account)
        except ObjectDoesNotExist:
            errors.append({"sub_account": f"SubAccount '{sub_account}' not found"})
            raise ViewException(
                code="6402", message=f'RateSheetUpload: SubAccount: \'{sub_account}\' not found', errors=errors
            )

        try:
            carrier = Carrier.objects.get(code=carrier_code)
        except ObjectDoesNotExist:
            errors.append({"carrier": f"Carrier with carrier code '{carrier_code}' not found"})
            raise ViewException(code="6403", message=f'RateSheetUpload: Carrier not found', errors=errors)

        try:
            NewRateSheetManagement(
                sub_account=sub_account,
                carrier=carrier,
                service_code=validated_data["service_code"],
                service_name=validated_data["service_name"],
                rs_type=validated_data["rs_type"],
            ).import_rate_sheet(
                workbook=ws,
            )
        except ViewException as e:
            raise ViewException(code=e.code, message=e.message, errors=e.errors)
        except Exception as e:
            errors.append({"rate_sheet_upload": f"Import Error {str(e.__class__.__name__)}."})
            raise ViewException(code="6404", message=f'RateSheetUpload: Import Error', errors=errors)

        return {"message": "Rate sheet has been uploaded."}
