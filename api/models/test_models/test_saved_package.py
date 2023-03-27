"""
    Title: Saved Package Model Unit Tests
    Description: This file will contain all unit tests for saved packages Model.
    Created: October 25, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.test import TestCase

from api.models import SubAccount
from api.models.saved_package import SavedPackage


class SavedPackageTests(TestCase):
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
        "subaccount"
    ]

    def setUp(self):
        self.sub_account = SubAccount.objects.first()

        self.saved_package_json = {
            "sub_account": self.sub_account,
            "package_type": "NORM_BOX",
            "description": "TEST",
            "length": Decimal("10.00"),
            "width": Decimal("10.00"),
            "height": Decimal("10.00"),
            "weight": Decimal("10.00"),
        }


    def test_all_fields_verbose(self):
        record = SavedPackage(**self.saved_package_json)

        self.assertIsInstance(record, SavedPackage)
        self.assertEqual(record.sub_account, self.sub_account)
        self.assertEqual(record.width,  Decimal("10.00"))
        self.assertEqual(record.length, Decimal("10.00"))
        self.assertEqual(record.height, Decimal("10.00"))
        self.assertEqual(record.weight, Decimal("10.00"))
        self.assertEqual(record.description, "TEST")
        self.assertEqual(record.package_type, "NORM_BOX")

    def test_repr(self):
        expected = "< Saved Package (kenneth carmichael: 10.00x10.00x10.00, 10.00 >"
        record = SavedPackage(**self.saved_package_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "kenneth carmichael: 10.00x10.00x10.00, 10.00"
        record = SavedPackage(**self.saved_package_json)
        self.assertEqual(expected, str(record))

