from decimal import Decimal

from django.test import TestCase

from api.models import Account, PackageType


class PackageTypesTests(TestCase):

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
        self.account = Account.objects.first()

        self.package_json = {
            "account":  self.account,
            "code": "BOX",
            "name": "Package",
            "min_overall_dims": Decimal("0.00"),
            "max_overall_dims": Decimal("150.00"),
            "min_weight": Decimal("0.00"),
            "max_weight": Decimal("100.00"),
            "is_common": False,
            "is_dangerous_good": True,
            "is_pharma": False,
            "is_active": True,
        }

    def test_create_empty(self):
        record = PackageType.create()
        self.assertIsInstance(record, PackageType)

    def test_create_full(self):
        record = PackageType.create(self.package_json)
        self.assertIsInstance(record, PackageType)

    def test_set_values(self):
        record = PackageType.create()
        record.set_values(self.package_json)
        self.assertEqual("BOX", record.code)
        self.assertEqual("Package", record.name)
        self.assertEqual(Decimal("150.00"), record.max_overall_dims)
        self.assertFalse(record.is_common)
        self.assertTrue(record.is_active)
        self.assertTrue(record.is_dangerous_good)
        self.assertFalse(record.is_pharma)

    def test_all_fields_verbose(self):
        record = PackageType(**self.package_json)

        self.assertIsInstance(record.account, Account)
        self.assertEqual("BOX", record.code)
        self.assertEqual("Package", record.name)
        self.assertEqual(Decimal("0.00"), record.min_overall_dims)
        self.assertEqual(Decimal("150.00"), record.max_overall_dims)
        self.assertEqual(Decimal("0.00"), record.min_weight)
        self.assertEqual(Decimal("100.00"), record.max_weight)
        self.assertFalse(record.is_common)
        self.assertTrue(record.is_active)
        self.assertTrue(record.is_dangerous_good)
        self.assertFalse(record.is_pharma)

    def test_repr(self):
        expected = '< PackageType (gobox: Package, False, True) >'
        record = PackageType.create(self.package_json)
        record.account = self.account
        self.assertEqual(repr(record), expected)

    def test_str(self):
        expected = 'gobox: Package, Common: False, Active: True'
        record = PackageType.create(self.package_json)
        record.account = self.account
        self.assertEqual(str(record), expected)

    def test_save(self):
        record = PackageType(**self.package_json)
        record.save()

        self.assertEqual("BOX", record.code)
        self.assertEqual("Package", record.name)
        self.assertEqual(Decimal("0.00"), record.min_overall_dims)
        self.assertEqual(Decimal("150.00"), record.max_overall_dims)
        self.assertEqual(Decimal("0.00"), record.min_weight)
        self.assertEqual(Decimal("100.00"), record.max_weight)
        self.assertFalse(record.is_common)
        self.assertTrue(record.is_active)
        self.assertTrue(record.is_dangerous_good)
        self.assertFalse(record.is_pharma)
