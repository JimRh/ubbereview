from decimal import Decimal

from django.test import TestCase

from api.apis.google.route_apis.distance_api import GoogleDistanceApi
from api.exceptions.project import ViewException
from api.models import LocationDistance


class GoogleDistanceApiTests(TestCase):

    fixtures = [
        "countries",
        "provinces",
        "addresses",
        "location_city",
        "location_distance"
    ]

    def setUp(self):
        self.distance_api = GoogleDistanceApi()

        self.distance_api._o_city = "calgary"
        self.distance_api._d_city = "whitehorse"
        self.distance_api._o_province = "AB"
        self.distance_api._d_province = "YT"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

    def test_check_city_alias(self):
        self.distance_api._check_city_alias()

        self.assertEqual("calgary", self.distance_api._o_city)
        self.assertEqual("whitehorse", self.distance_api._d_city)

    def test_check_city_alias_two(self):
        self.distance_api._o_city = "edm int'l airport"
        self.distance_api._d_city = "whitehorse"

        self.distance_api._check_city_alias()

        self.assertEqual("Edmonton International Airport", self.distance_api._o_city)
        self.assertEqual("whitehorse", self.distance_api._d_city)

    def test_get_location_distance(self):
        self.distance_api._o_city = "edmonton international airport"
        self.distance_api._d_city = "ottawa"
        self.distance_api._o_province = "AB"
        self.distance_api._d_province = "ON"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        location = self.distance_api._get_location_distance()

        self.assertIsInstance(location, LocationDistance)

    def test_get_location_distance_reverse(self):
        self.distance_api._d_city = "edmonton international airport"
        self.distance_api._o_city = "ottawa"
        self.distance_api._d_province = "AB"
        self.distance_api._o_province = "ON"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        location = self.distance_api._get_location_distance()

        self.assertIsInstance(location, LocationDistance)

    def test_get_location_distance_none(self):
        self.distance_api._d_city = "edmonton international airport"
        self.distance_api._o_city = "ottawa"
        self.distance_api._d_province = "AB"
        self.distance_api._o_province = "SK"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        location = self.distance_api._get_location_distance()

        self.assertIsNone(location)

    def test_save_distance(self):
        self.distance_api._d_city = "edmonton"
        self.distance_api._o_city = "ottawa"
        self.distance_api._d_province = "AB"
        self.distance_api._o_province = "ON"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        location = self.distance_api._save_distance({"distance": 1220, "duration": 1420})

        self.assertIsInstance(location, LocationDistance)
        self.assertEqual(Decimal("1220.00"), location.distance)
        self.assertEqual(Decimal("1420.00"), location.duration)
        self.assertEqual("edmonton", location.destination_city)
        self.assertEqual("ottawa", location.origin_city)

    def test_save_distance_o_province_fail(self):
        self.distance_api._d_city = "edmonton"
        self.distance_api._o_city = "ottawa"
        self.distance_api._d_province = "AB"
        self.distance_api._o_province = "ZZ"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        with self.assertRaises(ViewException) as context:
            location = self.distance_api._save_distance({"distance": 1220, "duration": 1420})

        self.assertEqual('LocationDistance Error: Province matching query does not exist.', context.exception.message)

    def test_save_distance_d_province_fail(self):
        self.distance_api._d_city = "edmonton"
        self.distance_api._o_city = "ottawa"
        self.distance_api._d_province = "ZZ"
        self.distance_api._o_province = "ON"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        with self.assertRaises(ViewException) as context:
            location = self.distance_api._save_distance({"distance": 1220, "duration": 1420})

        self.assertEqual('LocationDistance Error: Province matching query does not exist.', context.exception.message)

    def test_save_distance_fail(self):
        self.distance_api._d_city = "edmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmontonedmonton"
        self.distance_api._o_city = "ottawa"
        self.distance_api._d_province = "AB"
        self.distance_api._o_province = "ON"
        self.distance_api._o_country = "CA"
        self.distance_api._d_country = "CA"

        with self.assertRaises(ViewException) as context:
            location = self.distance_api._save_distance({"distance": 1220, "duration": 1420})

        self.assertEqual("LocationDistance Error: {'destination_city': ['Ensure this value has at most 100 characters (it has 528).']}", context.exception.message)
