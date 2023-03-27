"""
    Title: Saved Address Tests
    Description:  Saved Address Tests of all methods.
    Created: February 06, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""

from django.test import TestCase
from api.models import SubAccount, Address, Province
from apps.books.models import SavedAddress


class SavedAddressTest(TestCase):
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
        Saved Address model test setup
        """
        self.account = SubAccount.objects.first()
        self.address = Address.objects.first()
        self.address_last = Address.objects.last()
        self.province = Province.objects.first()

        self.save_address_full_json = {
            "account": self.account,
            "address_hash": "qwefvjnsvk",
            "name": "name three",
            "username": "test123",
            "address": self.address,
            "is_origin": True,
            "is_destination": True,
            "is_vendor": True,
        }

        self.save_address_json = {
            "account": self.account,
            "name": "name address",
            "username": "test1234",
            "address": self.address_last,
        }

    def test_create_empty(self):
        """
        Tests creating an empty saved address
        """
        record = SavedAddress.create()
        self.assertIsInstance(record, SavedAddress)

    def test_create_full(self):
        """
        Tests creating a saved address using all required details
        """
        record = SavedAddress.create(param_dict=self.save_address_full_json)
        self.assertIsInstance(record, SavedAddress)

    def test_create(self):
        """
        Tests creating a saved address using some required details

        """
        record = SavedAddress.create(param_dict=self.save_address_json)
        self.assertIsInstance(record, SavedAddress)

    def test_set_values(self):
        """
        Tests Saved Address set value method

        """
        record = SavedAddress.create()
        record.set_values(pairs=self.save_address_full_json)
        record.address = self.save_address_full_json["address"]

        self.assertEqual(record.name, "name three")
        self.assertEqual(record.username, "test123")
        self.assertEqual(record.address, self.address)
        self.assertEqual(record.is_origin, True)
        self.assertEqual(record.is_destination, True)
        self.assertEqual(record.is_vendor, True)

    def test_all_fields_verbose(self):
        """
        Tests all fields in a created saved address
        """
        record = SavedAddress.create(self.save_address_json)

        self.assertEqual(record.name, "name address")
        self.assertEqual(record.username, "test1234")
        self.assertEqual(record.address, self.address_last)
        self.assertEqual(record.is_origin, False)
        self.assertEqual(record.is_destination, False)
        self.assertEqual(record.is_vendor, False)

    def test_str(self):
        """
        Tests Saved Address str method
        """
        record = SavedAddress.create(self.save_address_full_json)
        record.account = self.account
        record.save()

        expected = "kenneth carmichael: 130 9 Avenue Se, Calgary, Alberta, Canada, T2G0P3, Origin: True, Destination: True"

        self.assertEqual(str(record), expected)

    def test_repr(self):
        """
        Tests Saved Address repr method
        """
        record = SavedAddress.create(self.save_address_full_json)
        record.account = self.account
        record.save()

        expected = "< SavedAddress (< SubAccount (8cd0cae7-6a22-4477-97e1-a7ccfbed3e01) >: 130 9 Avenue Se, Calgary, Alberta, Canada, T2G0P3, Origin True, Destination True"

        self.assertEqual(repr(record), expected)
