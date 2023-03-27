"""
    Title: Carrier Pickup Serializer Tests
    Description: This file will contain all functions for Carrier Pickup Serializer Tests.
    Created: August 15, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
import datetime

from django.test import TestCase

from api.apis.pickup.pickup_validate import PickupValidate
from api.exceptions.project import PickupException


class CarrierPickupSerializerTests(TestCase):

    fixtures = [
        "carriers",
        "carrier_pickup",
        "countries",
        "provinces",
        "city"
    ]

    def setUp(self):
        self.today = datetime.datetime.now().date()

        self.pickup_json = {
            "carrier_id": 20,
            "date": self.today,
            "start_time": "13:00",
            "end_time": "15:00",
            "city": "edmonton",
            "province": "AB",
            "country": "CA"
        }

    def test_validate_carrier(self):
        """
            Test for valid pickup carrier restriction
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["date"] = self.today + datetime.timedelta(days=1)

        ret = PickupValidate(pickup_request=copied).validate()

        self.assertTrue(ret)

    def test_validate_defaults(self):
        """
            Test for valid pickup defaults
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["carrier_id"] = 2
        copied["date"] = self.today + datetime.timedelta(days=1)

        ret = PickupValidate(pickup_request=copied).validate()

        self.assertTrue(ret)

    def test_validate_carrier_bad_date_past(self):
        """
            Test for bad date past
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["date"] = self.today - datetime.timedelta(days=5)

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertEqual(e.exception.message, "Pickup Validate: Pickup Date cannot be in the past.")

    def test_validate_carrier_bad_date_future(self):
        """
            Test for bad date future
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["date"] = self.today + datetime.timedelta(days=50)

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertEqual(e.exception.message, "Pickup Validate: Pickup Date is too far into the future.")

    def test_validate_carrier_bad_start_time_min(self):
        """
            Test for bad start time
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["start_time"] = "04:00"

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertEqual(e.exception.message, "Pickup Validate: Start Time in the Past.")

    def test_validate_carrier_bad_start_time_max(self):
        """
            Test for bad start time
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["start_time"] = "23:00"

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertEqual(e.exception.message, "Pickup Validate: Invalid 'start time.")

    def test_validate_carrier_bad_end_time_min(self):
        """
            Test for bad end time
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["end_time"] = "04:00"

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertIsInstance(e.exception.message, str)

    def test_validate_carrier_bad_end_time_max(self):
        """
            Test for bad end time
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["end_time"] = "23:00"

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertIsInstance(e.exception.message, str)

    def test_validate_carrier_bad_pickup_window(self):
        """
            Test for bad end time
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["carrier_id"] = 2
        copied["start_time"] = "13:00"
        copied["end_time"] = "14:00"

        with self.assertRaises(PickupException) as e:

            ret = PickupValidate(pickup_request=copied).validate()

        self.assertIsInstance(e.exception.message, str)
