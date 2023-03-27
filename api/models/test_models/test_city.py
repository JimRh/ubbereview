from django.test import TestCase

from api.models import City, Province, Address


class CityTests(TestCase):
    fixtures = [
        "countries",
        "provinces",
        "addresses"
    ]

    def setUp(self):
        self.province = Province.objects.get(code="AB", country__code="CA")
        self.airport_address = Address.objects.first()
        self.city_json = {
            "name": "Edmonton",
            "aliases": "",
            "province": Province.objects.get(code="AB", country__code="CA"),
            "google_place_id": "ChIJI__egEUioFMRXRX2SgygH0E",
            "timezone": "America/Edmonton",
            "timezone_name": "Mountain Daylight Time",
            "timezone_dst_off_set": 3600,
            "timezone_raw_off_set": -25200,
            "latitude": "53.5461245",
            "longitude": "-113.4938229",
            "airport_code": "YEG",
            "airport_name": "Edmonton International Airport",
            "airport_address": self.airport_address,
            "has_airport": True,
            "has_port": False
        }

        self.city_min_json = {
            "name": "Edmonton",
            "province": Province.objects.get(code="AB", country__code="CA"),
        }

    def test_call_empty(self):
        record = City.create()
        self.assertIsInstance(record, City)

    def test_call_full(self):
        record = City.create(self.city_json)
        self.assertIsInstance(record, City)

    def test_set_values(self):
        record = City.create()
        record.set_values(self.city_json)
        record.province = self.province
        record.airport_address = self.airport_address

        self.assertIsInstance(record, City)
        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.aliases, "")
        self.assertEqual(record.province, self.province)
        self.assertEqual(record.google_place_id, "ChIJI__egEUioFMRXRX2SgygH0E")
        self.assertEqual(record.timezone, "America/Edmonton")
        self.assertEqual(record.timezone_name, "Mountain Daylight Time")
        self.assertEqual(record.timezone_dst_off_set, 3600)
        self.assertEqual(record.timezone_raw_off_set, -25200)
        self.assertEqual(record.latitude, "53.5461245")
        self.assertEqual(record.longitude, "-113.4938229")
        self.assertEqual(record.airport_code, "YEG")
        self.assertEqual(record.airport_name, "Edmonton International Airport")
        self.assertEqual(record.airport_address, self.airport_address)
        self.assertTrue(record.has_airport)
        self.assertFalse(record.has_port)

    def test_all_fields_verbose(self):
        record = City.create(self.city_json)

        self.assertIsInstance(record, City)
        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.aliases, "")
        self.assertEqual(record.province, self.province)
        self.assertEqual(record.google_place_id, "ChIJI__egEUioFMRXRX2SgygH0E")
        self.assertEqual(record.timezone, "America/Edmonton")
        self.assertEqual(record.timezone_name, "Mountain Daylight Time")
        self.assertEqual(record.timezone_dst_off_set, 3600)
        self.assertEqual(record.timezone_raw_off_set, -25200)
        self.assertEqual(record.latitude, "53.5461245")
        self.assertEqual(record.longitude, "-113.4938229")
        self.assertEqual(record.airport_code, "YEG")
        self.assertEqual(record.airport_name, "Edmonton International Airport")
        self.assertEqual(record.airport_address, self.airport_address)
        self.assertTrue(record.has_airport)
        self.assertFalse(record.has_port)

    def test_repr(self):
        expected = "< City (Edmonton: Alberta, Canada, America/Edmonton, Lat: 53.5461245, Long: -113.4938229) >"
        record = City.create(self.city_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Edmonton: Alberta, Canada, America/Edmonton, Lat: 53.5461245, Long: -113.4938229"
        record = City.create(self.city_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = City.create(self.city_json)
        record.save()

        self.assertIsInstance(record, City)
        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.aliases, "")
        self.assertEqual(record.province, self.province)
        self.assertEqual(record.google_place_id, "ChIJI__egEUioFMRXRX2SgygH0E")
        self.assertEqual(record.timezone, "America/Edmonton")
        self.assertEqual(record.timezone_name, "Mountain Daylight Time")
        self.assertEqual(record.timezone_dst_off_set, 3600)
        self.assertEqual(record.timezone_raw_off_set, -25200)
        self.assertEqual(record.latitude, "53.5461245")
        self.assertEqual(record.longitude, "-113.4938229")
        self.assertEqual(record.airport_code, "YEG")
        self.assertEqual(record.airport_name, "Edmonton International Airport")
        self.assertEqual(record.airport_address, self.airport_address)
        self.assertTrue(record.has_airport)
        self.assertFalse(record.has_port)

    def test_save_min(self):
        record = City.create(self.city_min_json)
        record.save()

        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.aliases, "")
        self.assertEqual(record.province, self.province)
