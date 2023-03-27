
from django.test import TestCase

from api.models import MiddleLocation, Address


class MiddleLocationTests(TestCase):

    fixtures = [
        "countries",
        "provinces",
        "addresses",
        "middle_location"
    ]

    def setUp(self):
        self.address = Address.objects.last()

        self.location_json = {
            "address": self.address,
            "code": "YOW",
            "email": "bbe@bbex.com",
            "is_available": True
        }

    def test_create_empty(self):
        record = MiddleLocation.create()
        self.assertIsInstance(record, MiddleLocation)

    def test_create_full(self):
        record = MiddleLocation.create(self.location_json)
        self.assertIsInstance(record, MiddleLocation)

    def test_set_values(self):
        record = MiddleLocation.create()
        record.set_values(self.location_json)
        self.assertEqual(record.code, "YOW")
        self.assertTrue(record.is_available)

    def test_all_fields_verbose(self):
        record = MiddleLocation(**self.location_json)
        self.assertEqual(record.code, "YOW")
        self.assertTrue(record.is_available)
        self.assertIsInstance(record.address, Address)

    def test_repr(self):
        expected = '< MiddleLocation (YOW, Saskatoon, CA) >'
        record = MiddleLocation.create(self.location_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'YOW, Saskatoon, CA'
        record = MiddleLocation.create(self.location_json)
        self.assertEqual(expected, str(record))

    def test_get_ship_dict(self):
        expected = {
            'address': '2515 Airport Drive',
            'city': 'Saskatoon',
            'province': 'SK',
            'country': 'CA',
            'email': 'bbe@bbex.com',
            'postal_code': 'S7L7L1',
            'base': 'YOW'
        }
        record = MiddleLocation.create(self.location_json)
        self.assertDictEqual(record.get_ship_dict, expected)

    def test_save(self):
        record = MiddleLocation(**self.location_json)
        record.save()

        self.assertEqual(record.address, self.address)
        self.assertEqual(record.code, "YOW")
        self.assertTrue(record.is_available)

    def test_repr_two(self):
        expected = '< MiddleLocation (YEG, Edmonton, CA) >'
        record = MiddleLocation.objects.first()
        self.assertEqual(expected, repr(record))

    def test_str_two(self):
        expected = 'YEG, Edmonton, CA'
        record = MiddleLocation.objects.first()
        self.assertEqual(expected, str(record))
