"""
    Title: Saved Address Serializer Tests
    Description: This file will contain all Saved Address Serializer Tests
    Created: February 7, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import copy
from collections import OrderedDict

from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from api.models import SubAccount, Address
from apps.books.models import SavedAddress
from apps.books.serializers.saved_address_serializer import (
    SavedAddressSerializer,
    CreateSavedAddressSerializer,
    UploadSavedAddressSerializer,
)


class SavedAddressSerializerTests(TestCase):
    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "user",
        "group",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount",
    ]

    def setUp(self):
        """
        Saved Address Serializer Tests Setup
        """
        self.sub_account = SubAccount.objects.first()
        self.address = Address.objects.first()

        self.saved_address_json = {
            "account": self.sub_account,
            "address_hash": "qwefvjnsvk",
            "name": "name three",
            "username": "test123",
            "address": self.address,
            "is_origin": True,
            "is_destination": True,
            "is_vendor": True,
        }

        self.record = SavedAddress.create(param_dict=self.saved_address_json)
        self.record.save()

        self.create_saved_address_json = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
            "name": "test_name",
            "address_hash": "qwefvjnsvk",
            "address": {
                "address": "1759-25 Ave E",
                "address_two": "",
                "city": "Edmonton Internation Airport",
                "province": "AB",
                "country": "CA",
                "postal_code": "T9E0V6",
                "has_shipping_bays": True,
            },
            "is_origin": True,
            "is_destination": False,
            "is_vendor": False,
        }

        self.update_saved_address_json = {
            "name": "test_name",
            "username": "gobox",
            "address": {
                "address": "1759-25 Ave E",
                "address_two": "",
                "city": "Edmonton Internation Airport",
                "province": "AB",
                "country": "CA",
                "postal_code": "T9E0V6",
                "has_shipping_bays": True,
            },
            "is_origin": True,
            "is_destination": False,
            "is_vendor": False,
        }

        self.upload_saved_address_json = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
            "file": "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",
            "is_vendor": False,
        }

    def test_get_all(self):
        """
        Tests SavedAddressSerializer get all
        """
        expected = [
            OrderedDict(
                [
                    ("id", 1),
                    ("username", "test123"),
                    ("name", "name three"),
                    (
                        "address",
                        OrderedDict(
                            [
                                ("id", 7),
                                ("address", "130 9 Avenue Se"),
                                ("address_two", ""),
                                ("city", "Calgary"),
                                ("province", "AB"),
                                ("country", "CA"),
                                ("postal_code", "T2G0P3"),
                                ("has_shipping_bays", True),
                            ]
                        ),
                    ),
                    ("is_origin", True),
                    ("is_destination", True),
                    ("is_vendor", True),
                ]
            )
        ]
        serializer = SavedAddressSerializer(SavedAddress.objects.all(), many=True)
        ret = serializer.data

        self.assertIsInstance(ret, list)
        self.assertListEqual(ret, expected)

    def test_create(self):
        """
        Create Saved Address test
        """
        expected = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
            "name": "test_name",
            "address": OrderedDict(
                [
                    ("id", 62),
                    ("address", "1759-25 Ave E"),
                    ("address_two", ""),
                    ("city", "Edmonton Internation Airport"),
                    ("province", "AB"),
                    ("country", "CA"),
                    ("postal_code", "T9E0V6"),
                    ("has_shipping_bays", True),
                ]
            ),
            "is_origin": True,
            "is_destination": False,
            "is_vendor": False,
        }
        serializer = CreateSavedAddressSerializer(
            data=self.create_saved_address_json, many=False
        )

        if serializer.is_valid():
            serializer.create(validated_data=serializer.validated_data)
            ret = serializer.data

            self.assertIsInstance(ret, dict)
            self.assertDictEqual(ret, expected)

    def test_create_fail_sub_account(self):
        """
        Create Saved Address Fail On Sub Account
        """
        copied = copy.deepcopy(self.create_saved_address_json)
        copied["account_number"] = "8cd0cae5-6a22-4477-97e1-a7ccfbed3e02"

        serializer = CreateSavedAddressSerializer(data=copied, many=False)

        with self.assertRaises(serializers.ValidationError) as e:
            if serializer.is_valid():
                serializer.create(validated_data=serializer.validated_data)

        expected = {
            "account": [ErrorDetail(string="Account not found.", code="invalid")]
        }

        self.assertEqual(e.exception.detail, expected)

    def test_create_fail_province(self):
        """
        Create Saved Address Fail On Province
        """
        copied = copy.deepcopy(self.create_saved_address_json)
        copied["address"]["province"] = "AA"

        serializer = CreateSavedAddressSerializer(data=copied, many=False)

        if serializer.is_valid():
            serializer.create(validated_data=serializer.validated_data)

        expected = {'address': {'province': [ErrorDetail(string="Not found with 'code': AA and 'country': CA.", code='invalid')]}}

        self.assertEqual(serializer.errors, expected)

    def test_update(self):
        """
        Update Saved Address Test
        """
        expected = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
            "name": "test_name",
            "address": OrderedDict(
                [
                    ("id", 62),
                    ("address", "1759-25 Avenue E"),
                    ("address_two", ""),
                    ("city", "Edmonton Internation Airport"),
                    ("province", "AB"),
                    ("country", "CA"),
                    ("postal_code", "T9E0V6"),
                    ("has_shipping_bays", True),
                ]
            ),
            "is_origin": True,
            "is_destination": False,
            "is_vendor": False,
        }

        serializer = SavedAddressSerializer(
            data=self.update_saved_address_json, many=False
        )
        address = SavedAddress.objects.first()

        if serializer.is_valid():
            instance = serializer.update(
                instance=address, validated_data=serializer.validated_data
            )

            self.assertIsInstance(instance, SavedAddress)
            self.assertEqual(instance.name, "test_name")

    def test_update_fail_province(self):
        """
        Update Saved Address Fail On Province
        """
        copied = copy.deepcopy(self.update_saved_address_json)
        copied["address"]["province"] = "AA"
        copied["address"]["country"] = "ZZ"
        serializer = SavedAddressSerializer(data=copied, many=False)
        address = SavedAddress.objects.get(pk="1")

        with self.assertRaises(serializers.ValidationError) as e:
            if serializer.is_valid():
                serializer.update(
                    validated_data=serializer.validated_data, instance=address
                )

        expected = {
            "province": [
                ErrorDetail(
                    string="Not found with 'code': AA and 'country': ZZ.",
                    code="invalid",
                )
            ]
        }

        self.assertEqual(e.exception.detail, expected)

    def test_upload(self):
        """
        Upload Saved Address Test
        """
        expected = {"message": "Saved Address has been uploaded."}

        serializer = UploadSavedAddressSerializer(
            data=self.upload_saved_address_json, many=False
        )

        if serializer.is_valid():
            serializer.validated_data["account"] = self.sub_account
            ret = serializer.create(validated_data=serializer.validated_data)

            self.assertIsInstance(ret, dict)
            self.assertEqual(ret, expected)

    def test_upload_fail_province(self):
        """
        Upload Saved Address Fail On Province
        """
        copied = copy.deepcopy(self.upload_saved_address_json)
        copied[
            "file"
        ] = "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"
        serializer = UploadSavedAddressSerializer(data=copied, many=False)

        with self.assertRaises(serializers.ValidationError) as e:
            if serializer.is_valid():
                serializer.create(validated_data=serializer.validated_data)

        expected = {
            "province": [
                ErrorDetail(
                    string="Row: 1 - Not found with 'code': NONE and 'country code': CA.",
                    code="invalid",
                )
            ]
        }

        self.assertEqual(e.exception.detail, expected)
