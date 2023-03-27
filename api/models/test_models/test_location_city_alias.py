
from django.test import TestCase

from api.models import LocationCityAlias, Province


class LocationCityAliasTests(TestCase):

    fixtures = [
        "countries",
        "provinces",
        "location_city"
    ]

    def setUp(self):
        self.province = Province.objects.first()

        self.alias_json = {
            "province": self.province,
            "name": "Edmonton",
            "alias": "edm"
        }

    def test_create_empty(self):
        record = LocationCityAlias.create()
        self.assertIsInstance(record, LocationCityAlias)

    def test_create_full(self):
        record = LocationCityAlias.create(self.alias_json)
        self.assertIsInstance(record, LocationCityAlias)

    def test_set_values(self):
        record = LocationCityAlias.create()
        record.set_values(self.alias_json)
        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.alias, "edm")

    def test_all_fields_verbose(self):
        record = LocationCityAlias(**self.alias_json)
        record.save()
        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.alias, "edm")
        self.assertIsInstance(record.province, Province)

    def test_repr(self):
        expected = '< LocationCityAlias (Alberta, Canada: Edmonton, edm) >'
        record = LocationCityAlias.create(self.alias_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'Alberta, Canada: Edmonton, edm'
        record = LocationCityAlias.create(self.alias_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = LocationCityAlias(**self.alias_json)
        record.save()

        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.alias, "edm")
        self.assertIsInstance(record.province, Province)

    def test_repr_two(self):
        expected = '< LocationCityAlias (Alberta, Canada: Edmonton International Airport, edm int\'l airport) >'
        record = LocationCityAlias.objects.first()
        self.assertEqual(expected, repr(record))

    def test_str_two(self):
        expected = 'Alberta, Canada: Edmonton International Airport, edm int\'l airport'
        record = LocationCityAlias.objects.first()
        self.assertEqual(expected, str(record))
