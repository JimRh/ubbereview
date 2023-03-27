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

from api.apis.pickup.pickup import Pickup
from api.exceptions.project import PickupException
from api.models import Leg, API


class TestPickup(TestCase):

    fixtures = [
        "api",
        "countries",
        "provinces",
        "addresses",
        "carriers",
        "contact",
        "user",
        "group",
        "subaccount",
        "encryted_messages",
        "carrier_account",
        "account",
        "markup",
        "shipments",
        "legs"
    ]

    def setUp(self):
        self.today = datetime.datetime.now().date()
        self.leg = Leg.objects.first()

        self.pickup_json = {
            "leg_id": self.leg.leg_id,
            "date": self.today,
            "start_time": "12:00",
            "end_time": "15:00",
            "special_instructions": "Am Pickup Instructions"
        }

    def test_get_leg(self):
        """
        Test get leg object for leg id
        :return:
        """

        pickup = Pickup(ubbe_request=self.pickup_json)
        leg = pickup._get_leg()

        self.assertIsInstance(leg, Leg)

    def test_get_leg_fail(self):
        """
        Test get leg object for bad leg id
        :return:
        """
        copied = copy.deepcopy(self.pickup_json)
        copied["leg_id"] = "ub123456789P"

        with self.assertRaises(PickupException) as e:

            pickup = Pickup(ubbe_request=copied)
            leg = pickup._get_leg()

        self.assertEqual(e.exception.message, "Pickup: Leg not found for 'ub123456789P'.")

    def test_get_carrier_api(self):
        """
        Test get leg object amd carrier api.
        :return:
        """

        pickup = Pickup(ubbe_request=self.pickup_json)
        leg, carrier_api = pickup._get_carrier_api()

        self.assertIsInstance(leg, Leg)
