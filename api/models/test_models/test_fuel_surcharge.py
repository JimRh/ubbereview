from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import Carrier, FuelSurcharge


class FuelSurchargeTests(TestCase):
    fixtures = [
        "carriers",
        "fuel_surcharge"
    ]
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    fuel_surcharge_json = {
        "carrier": carrier,
        "updated_date": "2018-05-03:2018-06-04",
        "ten_thou_under": Decimal("77.77"),
        "ten_thou_to_fifty_five_thou": Decimal("88.88"),
        "fifty_five_thou_greater": Decimal("99.99"),
        "fuel_type": "I"
    }

    def test_create_empty(self):
        record = FuelSurcharge.create()
        self.assertIsInstance(record, FuelSurcharge)

    def test_create_full(self):
        record = FuelSurcharge.create(self.fuel_surcharge_json)
        self.assertIsInstance(record, FuelSurcharge)

    def test_set_values(self):
        record = FuelSurcharge.create()
        record.set_values(self.fuel_surcharge_json)
        self.assertEqual(record.ten_thou_under, Decimal("77.77"))

    def test_all_fields_verbose(self):
        record = FuelSurcharge(**self.fuel_surcharge_json)
        self.assertEqual(record.updated_date, "2018-05-03:2018-06-04")
        self.assertEqual(record.ten_thou_under, Decimal("77.77"))
        self.assertEqual(record.ten_thou_to_fifty_five_thou, Decimal("88.88"))
        self.assertEqual(record.fifty_five_thou_greater, Decimal("99.99"))
        self.assertEqual(record.fuel_type, "I")
        self.assertIsInstance(record.carrier, Carrier)

    def test_repr(self):
        expected = "< FuelSurcharge (Manitoulin, Domestic) >"
        record = FuelSurcharge.objects.get(pk=2)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Manitoulin, Domestic"
        record = FuelSurcharge.objects.get(pk=2)
        self.assertEqual(expected, str(record))

    def test_save(self):
        fuel_surcharge_json_full = {
            "carrier": Carrier.objects.get(code=535),
            "updated_date": "2018-05-03:2018-06-04",
            "ten_thou_under": Decimal("77.77777"),
            "ten_thou_to_fifty_five_thou": Decimal("88.88888"),
            "fifty_five_thou_greater": Decimal("99.99999"),
            "fuel_type": "I"
        }
        record = FuelSurcharge(**fuel_surcharge_json_full)

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.updated_date, "2018-05-03:2018-06-04")
        self.assertEqual(record.ten_thou_under, Decimal("77.78"))
        self.assertEqual(record.ten_thou_to_fifty_five_thou, Decimal("88.89"))
        self.assertEqual(record.fifty_five_thou_greater, Decimal("100.00"))

    def test_get_json_error(self):
        record = FuelSurcharge.objects.get(pk=2)

        with self.assertRaises(ValueError):
            record.get_json(Decimal("-2.22"), Decimal("1.0"))

    def test_get_json_under_ten_thou(self):
        expected = {'carrier_id': 670, 'cost': Decimal('0.27'), 'fuel_type': 'D', 'name': 'Fuel Surcharge', 'percentage': Decimal('26.90'), 'valid_to': '', 'valid_from': ''}
        record = FuelSurcharge.objects.get(pk=12)
        self.assertDictEqual(expected, record.get_json(Decimal("10.00"), Decimal("1.0")))

    def test_get_json_over_fifty_five_thou(self):
        expected = {'carrier_id': 670, 'cost': Decimal('0.27'), 'fuel_type': 'D', 'name': 'Fuel Surcharge', 'percentage': Decimal('26.90'), 'valid_to': '', 'valid_from': ''}
        record = FuelSurcharge.objects.get(pk=12)

        self.assertDictEqual(expected, record.get_json(Decimal("2.22"), Decimal("1.0")))

    def test_get_json_over_ten_less_fifty_five_thou(self):
        expected = {'carrier_id': 670, 'cost': Decimal('0.27'), 'fuel_type': 'D', 'name': 'Fuel Surcharge', 'percentage': Decimal('26.90'), 'valid_to': '', 'valid_from': ''}
        record = FuelSurcharge.objects.get(pk=12)
        self.assertDictEqual(expected, record.get_json(Decimal("2.22"), Decimal("1.0")))

    def test_get_json_no_date(self):
        expected = {'carrier_id': 535, 'cost': Decimal('0.17'), 'fuel_type': 'D', 'name': 'Fuel Surcharge', 'percentage': Decimal('17.30'), 'valid_to': '', 'valid_from': ''}
        record = FuelSurcharge.objects.get(pk=2)

        self.assertDictEqual(expected, record.get_json(Decimal("10.00"), Decimal("1.0")))
