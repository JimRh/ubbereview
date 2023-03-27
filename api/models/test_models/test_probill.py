from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Carrier, ProBillNumber


class ProBillNumberTests(TestCase):
    fixtures = [
        "carriers"
    ]
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    probill_json = {
        "carrier": carrier,
        "probill_number": "TEST",
        "available": False
    }

    def test_create_empty(self):
        record = ProBillNumber.create()
        self.assertIsInstance(record, ProBillNumber)

    def test_create_full(self):
        record = ProBillNumber.create(self.probill_json)
        self.assertIsInstance(record, ProBillNumber)

    def test_set_values(self):
        record = ProBillNumber.create()
        record.set_values(self.probill_json)
        self.assertEqual(record.probill_number, "TEST")

    def test_all_fields_verbose(self):
        record = ProBillNumber(**self.probill_json)
        self.assertEqual(record.probill_number, "TEST")
        self.assertFalse(record.available)
        self.assertIsInstance(record.carrier, Carrier)

    def test_repr(self):
        expected = "< ProBillNumber (TEST) >"
        record = ProBillNumber.create(self.probill_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST"
        record = ProBillNumber.create(self.probill_json)
        self.assertEqual(expected, str(record))
