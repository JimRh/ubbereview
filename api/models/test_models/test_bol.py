
from django.test import TestCase

from api.models import Dispatch, BillOfLading


class BillOfLadingTests(TestCase):

    fixtures = [
        "carriers",
        "contact",
        "test_dispatch",
        "test_bol"
    ]

    def setUp(self):
        self.dispatch = Dispatch.objects.first()

        self.dispatch_json = {
            "dispatch": self.dispatch,
            "bill_of_lading": "1234567890",
            "is_available": True
        }

    def test_create_empty(self):
        record = BillOfLading.create()
        self.assertIsInstance(record, BillOfLading)

    def test_create_full(self):
        record = BillOfLading.create(self.dispatch_json)
        self.assertIsInstance(record, BillOfLading)

    def test_set_values(self):
        record = BillOfLading.create()
        record.set_values(self.dispatch_json)
        self.assertEqual(record.bill_of_lading, "1234567890")
        self.assertTrue(record.is_available)

    def test_all_fields_verbose(self):
        record = BillOfLading(**self.dispatch_json)
        self.assertEqual(record.bill_of_lading, "1234567890")
        self.assertTrue(record.is_available)
        self.assertIsInstance(record.dispatch, Dispatch)

    def test_repr(self):
        expected = '< BillOfLading (Action Express, Edmonton, Default: True, 1234567890, True) >'
        record = BillOfLading.create(self.dispatch_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'Action Express, Edmonton, Default: True, 1234567890, True'
        record = BillOfLading.create(self.dispatch_json)
        self.assertEqual(expected, str(record))

    def test_dispatch_carrier(self):
        expected = "Action Express"
        record = BillOfLading.objects.first()
        self.assertEqual(expected, record.dispatch_carrier)

    def test_dispatch_location(self):
        expected = 'Edmonton'
        record = BillOfLading.objects.first()
        self.assertEqual(expected, record.dispatch_location)
