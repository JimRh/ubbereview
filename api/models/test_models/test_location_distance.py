from decimal import Decimal

from django.test import TestCase

from api.models import LocationDistance, Province


class LocationDistanceTests(TestCase):

    fixtures = [
        "countries",
        "provinces",
        "addresses",
        "location_distance"
    ]

    def setUp(self):
        self.o_province = Province.objects.first()
        self.d_province = Province.objects.last()

        self.distance_json = {
            "origin_city": "Edmonton",
            "origin_province": self.o_province,
            "destination_city": "Calgary",
            "destination_province": self.d_province,
            "distance": "2000",
            "duration": "56"
        }

    def test_create_empty(self):
        record = LocationDistance.create()
        self.assertIsInstance(record, LocationDistance)

    def test_create_full(self):
        record = LocationDistance.create(self.distance_json)
        self.assertIsInstance(record, LocationDistance)

    def test_set_values(self):
        record = LocationDistance.create()
        record.set_values(self.distance_json)
        self.assertEqual(record.origin_city, "Edmonton")
        self.assertEqual(record.destination_city, "Calgary")
        self.assertEqual(record.distance, "2000")
        self.assertEqual(record.duration, "56")

    def test_all_fields_verbose(self):
        record = LocationDistance(**self.distance_json)

        self.assertEqual(record.origin_city, "Edmonton")
        self.assertEqual(record.destination_city, "Calgary")

        self.assertIsInstance(record.origin_province, Province)
        self.assertIsInstance(record.destination_province, Province)
        self.assertEqual(record.origin_province, self.o_province)
        self.assertEqual(record.destination_province, self.d_province)

        self.assertEqual(record.distance, "2000")
        self.assertEqual(record.duration, "56")

    def test_repr(self):
        expected = '< LocationDistance (Edmonton, AB, Calgary, YT, 2000) >'
        record = LocationDistance.create(self.distance_json)
        record.save()
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'Edmonton, AB, Calgary, YT, 2000'
        record = LocationDistance.create(self.distance_json)
        record.save()
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = LocationDistance(**self.distance_json)
        record.save()

        self.assertEqual(record.origin_city, "Edmonton")
        self.assertEqual(record.destination_city, "Calgary")

        self.assertIsInstance(record.origin_province, Province)
        self.assertIsInstance(record.destination_province, Province)
        self.assertEqual(record.origin_province, self.o_province)
        self.assertEqual(record.destination_province, self.d_province)

        self.assertEqual(record.distance, Decimal('2000'))
        self.assertEqual(record.duration, Decimal('56'))

    def test_repr_two(self):
        expected = '< LocationDistance (edmonton international airport, AB, ottawa, ON, 2846.00) >'
        record = LocationDistance.objects.first()
        self.assertEqual(expected, repr(record))

    def test_str_two(self):
        expected = 'edmonton international airport, AB, ottawa, ON, 2846.00'
        record = LocationDistance.objects.first()
        self.assertEqual(expected, str(record))
