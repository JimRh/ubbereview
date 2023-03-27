from decimal import Decimal

from django.test import TestCase

from api.models import Carrier, Airbase, CarrierMarkup


class CarrierTests(TestCase):
    fixtures = [
        "carriers",
        "user",
        "group",
        "account",
        "markup"
    ]
    carrier_json = {
        "code": 7,
        "name": "TEST",
        "email": "example@example.com",
        "linear_weight": Decimal("7.00"),
        "is_kilogram": True,
        "is_dangerous_good": True,
        'type': 'RS',
    }

    def test_create_empty(self):
        record = Carrier.create()
        self.assertIsInstance(record, Carrier)

    def test_create_full(self):
        record = Carrier.create(self.carrier_json)
        self.assertIsInstance(record, Carrier)

    def test_set_values(self):
        record = Carrier.create()
        record.set_values(self.carrier_json)
        self.assertEqual(record.name, "TEST")

    def test_all_fields_verbose(self):
        record = Carrier.create(self.carrier_json)
        self.assertEqual(record.code, 7)
        self.assertEqual(record.name, "TEST")
        self.assertEqual(record.email, "example@example.com")
        self.assertEqual(record.linear_weight, Decimal("7.00"))
        self.assertTrue(record.is_kilogram)
        self.assertTrue(record.type, "")
        self.assertTrue(record.mode, "")

    def test_repr(self):
        expected = "< Carrier (TEST: 7) >"
        record = Carrier.create(self.carrier_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST"
        record = Carrier.create(self.carrier_json)
        self.assertEqual(expected, str(record))
