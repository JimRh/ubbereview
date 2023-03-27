"""
    Title: Saved Address Serializer Tests
    Description: This file will contain all Saved Contact Serializer Tests
    Created: February 9, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import copy
from collections import OrderedDict

from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from api.models import SubAccount, Contact
from apps.books.models import SavedContact
from apps.books.serializers.saved_contact_serializer import (
    SavedContactSerializer,
    CreateSavedContactSerializer,
    UploadSavedContactSerializer,
)


class SavedContactSerializerTests(TestCase):

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
        Saved Contact Serializer Tests Setup
        """
        self.sub_account = SubAccount.objects.first()
        self.contact = Contact.objects.first()

        self.saved_contact_json = {
            "account": self.sub_account,
            "contact_hash": "adsjnnkl",
            "username": "test123",
            "contact": self.contact,
            "is_origin": True,
            "is_destination": True,
            "is_vendor": True,
        }

        self.record = SavedContact.create(param_dict=self.saved_contact_json)
        self.record.save()

        self.create_saved_contact_json = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "contact_hash": "adsjnnkl",
            "username": "gobox",
            "contact": {
                "company_name": "BBE Expediting Ltd",
                "name": "test",
                "phone": "7808908611",
                "email": "developer@bbex.com",
            },
            "is_origin": True,
            "is_destination": False,
            "is_vendor": False,
        }

        self.update_saved_contact_json = {
            "contact": {
                "company_name": "BBE Expediting Ltd",
                "name": "test",
                "phone": "7808908611",
                "email": "developer@bbex.com",
            },
            "is_origin": False,
            "is_destination": True,
            "is_vendor": True,
        }

        self.upload_saved_contact_json = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
            "file": "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",
            "is_vendor": False,
        }

    def test_get_all(self):
        """
        Tests SavedContactSerializer get all
        """
        expected = [
            OrderedDict(
                [
                    ("id", 1),
                    ("username", "test123"),
                    (
                        "contact",
                        OrderedDict(
                            [
                                ("id", 1),
                                ("company_name", "KenCar"),
                                ("name", "KenCar"),
                                ("phone", "7809326245"),
                                ("email", "developer@bbex.com"),
                            ]
                        ),
                    ),
                    ("is_origin", True),
                    ("is_destination", True),
                    ("is_vendor", True),
                ]
            )
        ]

        contact = SavedContact.objects.all()
        serializer = SavedContactSerializer(contact, many=True)
        ret = serializer.data
        self.assertIsInstance(ret, list)
        self.assertListEqual(ret, expected)

    def test_create(self):

        """
        Create Saved Contact test
        """
        expected = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
            "contact": OrderedDict(
                [
                    ("id", 10),
                    ("company_name", "BBE Expediting Ltd"),
                    ("name", "test"),
                    ("phone", "7808908611"),
                    ("email", "developer@bbex.com"),
                ]
            ),
            "is_origin": True,
            "is_destination": False,
            "is_vendor": False,
        }
        serializer = CreateSavedContactSerializer(
            data=self.create_saved_contact_json, many=False
        )

        if serializer.is_valid():
            serializer.create(validated_data=serializer.validated_data)
            ret = serializer.data

            self.assertIsInstance(ret, dict)
            self.assertDictEqual(ret, expected)

    def test_create_fail_sub_account(self):
        """
        Create Saved Contact Fail On Sub Account
        """
        copied = copy.deepcopy(self.create_saved_contact_json)
        copied["account_number"] = "8cd0cae5-6a22-4477-97e1-a7ccfbed3e02"

        serializer = CreateSavedContactSerializer(data=copied, many=False)

        with self.assertRaises(serializers.ValidationError) as e:
            if serializer.is_valid():
                serializer.create(validated_data=serializer.validated_data)

        expected = {'account': [ErrorDetail(string='Account not found.', code='invalid')]}

        self.assertEqual(e.exception.detail, expected)

    def test_update(self):
        """
        Update Saved Contact Test
        """
        expected = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "username": "gobox",
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
        serializer = SavedContactSerializer(data=self.update_saved_contact_json, many=False)
        contact = SavedContact.objects.first()

        if serializer.is_valid():
            instance = serializer.update(
                instance=contact, validated_data=serializer.validated_data
            )

            self.assertIsInstance(instance, SavedContact)
            self.assertEqual(instance, "test_name")

    def test_upload(self):
        """
        Upload Saved Contact Test
        """
        expected = {'message': 'Saved Contact has been uploaded.'}
        serializer = UploadSavedContactSerializer(
            data=self.upload_saved_contact_json, many=False
        )

        if serializer.is_valid():
            serializer.validated_data["account"] = self.sub_account
            ret = serializer.create(validated_data=serializer.validated_data)

            self.assertIsInstance(ret, dict)
            self.assertDictEqual(ret, expected)
