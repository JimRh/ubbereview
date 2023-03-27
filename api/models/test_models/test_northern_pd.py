from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import NorthernPDAddress


class NorthernPDAddressTests(TestCase):
    northern_pd_address_json = {
        "pickup_id": 1,
        "delivery_id": 2,
        "city_name": "TEST",
        "price_per_kg": Decimal("7.00"),
        "min_price": Decimal("7.00"),
        "cutoff_weight": Decimal("7.00")
    }

    def test_create_empty(self):
        record = NorthernPDAddress.create()
        self.assertIsInstance(record, NorthernPDAddress)

    def test_create_full(self):
        record = NorthernPDAddress.create(self.northern_pd_address_json)
        self.assertIsInstance(record, NorthernPDAddress)

    def test_set_values(self):
        record = NorthernPDAddress.create()
        record.set_values(self.northern_pd_address_json)
        self.assertEqual(record.min_price, Decimal("7.00"))

    def test_all_fields_verbose(self):
        record = NorthernPDAddress.create(self.northern_pd_address_json)
        self.assertEqual(record.pickup_id, 1)
        self.assertEqual(record.delivery_id, 2)
        self.assertEqual(record.city_name, "TEST")
        self.assertEqual(record.price_per_kg, Decimal("7.00"))
        self.assertEqual(record.min_price, Decimal("7.00"))
        self.assertEqual(record.cutoff_weight, Decimal("7.00"))

    def test_repr(self):
        expected = "< NorthernPDAddress (TEST, 7.00) >"
        record = NorthernPDAddress.create(self.northern_pd_address_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST, 7.00"
        record = NorthernPDAddress.create(self.northern_pd_address_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        northern_pd_address_json = {
            "address_id": 7,
            "city_name": "TEST",
            "price_per_kg": Decimal("7.7787"),
            "min_price": Decimal("7.2222"),
            "cutoff_weight": Decimal("7.7263"),
            "pickup_id": 1,
            "delivery_id": 2
        }
        record = NorthernPDAddress.create(northern_pd_address_json)
        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertEqual(record.pickup_id, 1)
        self.assertEqual(record.delivery_id, 2)
        self.assertEqual(record.city_name, "TEST")
        self.assertEqual(record.price_per_kg, Decimal("7.78"))
        self.assertEqual(record.min_price, Decimal("7.22"))
        self.assertEqual(record.cutoff_weight, Decimal("7.73"))
