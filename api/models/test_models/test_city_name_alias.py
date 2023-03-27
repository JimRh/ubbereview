from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import CityNameAlias, Carrier, Province


class CityNameAliasTests(TestCase):
    fixtures = [
        "carriers",
        "countries",
        "provinces"
    ]
    province = mock.Mock(spec=Province)
    province._state = Mock()
    province._state.db = None

    def setUp(self):
        self.city_name_json = {
            "name": "TEST",
            "alias": "TESTING",
            "province": self.province,
            "carrier": Carrier.objects.get(code=601)
        }

    def test_create_empty(self):
        record = CityNameAlias.create()
        self.assertIsInstance(record, CityNameAlias)

    def test_create_full(self):
        record = CityNameAlias.create(self.city_name_json)
        self.assertIsInstance(record, CityNameAlias)

    def test_set_values(self):
        record = CityNameAlias.create()
        record.set_values(self.city_name_json)
        self.assertEqual(record.name, "TEST")

    def test_all_fields_verbose(self):
        record = CityNameAlias(**self.city_name_json)
        self.assertIsInstance(record.province, Province)
        self.assertEqual(record.name, "TEST")
        self.assertEqual(record.alias, "TESTING")

    def test_repr(self):
        expected = "< CityAlias (Action Express: TEST, TESTING) >"
        record = CityNameAlias(**self.city_name_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Action Express: TEST, TESTING"
        record = CityNameAlias(**self.city_name_json)
        self.assertEqual(expected, str(record))

    def test_check_alias(self):
        city_name_json = {
            "name": "Edmonton",
            "alias": "Edmonton International Airport",
            "province": Province.objects.get(code="AB", country__code="CA"),
            "carrier": Carrier.objects.first()
        }
        city_name = CityNameAlias(**city_name_json)

        city_name.save()
        alias = CityNameAlias.check_alias("Edmonton International Airport", "AB", "CA", Carrier.objects.first().code)

        self.assertEqual(alias, "Edmonton")

    def test_check_alias_carrier(self):
        city_name_json = {
            "name": "Test",
            "alias": "Edmonton International Airport",
            "province": Province.objects.get(code="AB", country__code="CA"),
            "carrier": Carrier.objects.first()
        }

        city_name = CityNameAlias(**city_name_json)
        city_name.save()

        alias = CityNameAlias.check_alias("Edmonton International Airport", "AB", "CA", Carrier.objects.first().code)
        self.assertEqual(alias, "Test")
