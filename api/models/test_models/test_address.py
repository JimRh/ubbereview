from django.test import TestCase
from unittest import mock
from unittest.mock import Mock

from api.models import Address, Province, Country


# TODO: test: next_leg_json, find, clean_city, clean_postal_code, clean_address, get_ship_dict, clean
class AddressTests(TestCase):
    fixtures = [
        "countries",
        "provinces"
    ]
    province = mock.Mock(spec=Province)
    province._state = Mock()
    province._state.db = None
    address_json = {
        "province": province,
        "city": "TEST",
        "address": "TEST",
        "address_two": "TEST",
        "postal_code": "TEST",
        "has_shipping_bays": True
    }

    def setUp(self):
        self.address_json_full = {
            "province": Province.objects.get(code="AB", country__code="CA"),
            "city": "TEST",
            "address": "TEST",
            "address_two": "TEST",
            "postal_code": "TEST",
            "has_shipping_bays": True
        }

    def test_call_empty(self):
        record = Address.create()
        self.assertIsInstance(record, Address)

    def test_call_full(self):
        record = Address.create(self.address_json)
        self.assertIsInstance(record, Address)

    def test_set_values(self):
        record = Address.create()
        record.set_values(self.address_json)
        self.assertEqual(record.city, "TEST")

    def test_all_fields_verbose(self):
        record = Address.create(self.address_json)
        self.assertTrue(record.has_shipping_bays)
        self.assertEqual(record.city, "TEST")
        self.assertEqual(record.address, "TEST")
        self.assertEqual(record.address_two, "TEST")
        self.assertEqual(record.postal_code, "TEST")
        self.assertIsInstance(record.province, Province)

    def test_repr(self):
        expected = "< Address (TEST, TEST, < Province (Alberta: AB, Canada: CA) >, TEST) >"
        record = Address.create(self.address_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST, TEST, Alberta, Canada, TEST"
        record = Address.create(self.address_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        address_json = {
            "province": Province.objects.get(pk=1),
            "city": "Testerton",
            "address": "777 Test Street",
            "postal_code": "A1B2C3"
        }
        address = Address.create(address_json)

        address.save()
        self.assertIsInstance(Address.objects.get(address="777 Test St"), Address)
        self.assertEqual(Address.objects.get(address="777 Test St").address, "777 Test St")

    def test_create_or_find(self):
        address_json = {
            "country": Country.objects.get(pk=1).code,
            "province": Province.objects.get(pk=1).code,
            "city": "Testerton1",
            "address": "7777 Test Street",
            "postal_code": "A1B2C4"
        }
        address = Address.create_or_find(address_json)

        self.assertIsInstance(address, Address)
        self.assertIsInstance(Address.objects.get(address="7777 Test St"), Address)
        self.assertEqual(Address.objects.get(address="7777 Test St").address, "7777 Test St")

