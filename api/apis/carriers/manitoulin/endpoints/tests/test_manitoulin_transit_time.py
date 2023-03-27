"""
    Title: Manitoulin Transit Time Unit Tests
    Description: Unit Tests for  Manitoulin Transit Time. Test Everything.
    Created: January 09, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import copy
import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.manitoulin.endpoints.manitoulin_transit_time import (
    ManitoulinTransitTime,
)
from api.globals.carriers import MANITOULIN
from api.models import SubAccount, Carrier, CarrierAccount


class ManitoulinTransitTimeTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "user",
        "group",
        "markup",
        "carrier_markups",
        "account",
        "subaccount",
        "encryted_messages",
        "carrier_account",
        "northern_pd",
        "skyline_account",
        "nature_of_goods",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=MANITOULIN)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "pickup": {
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date()
            },
            "origin": {
                "address": "1759 35 Ave E",
                "city": "Edmonton International Airport",
                "province": "ON",
                "country": "CA",
                "postal_code": "T9E0V6",
                "is_residential": False,
                "tailgate_pickup": False,
                "flat_deck_pickup": False,
                "inside_pickup": False,
                "drop_off_at_terminal": False,
                "warehouse_pickup": False,
                "company_name": "BBE EXPEDITING LTD",
            },
            "destination": {
                "address": "800 Macleod Trail S.E",
                "city": "CALGARY",
                "province": "AB",
                "country": "CA",
                "postal_code": "T2P2M5",
                "residential_delivery": False,
                "tailgate_delivery": False,
                "flat_deck_delivery": False,
                "inside_delivery": False,
                "dock_pickup": False,
                "company_name": "TEST",
            },
            "packages": [
                {
                    "class_value": "70.00",
                    "quantity": 1,
                    "package_type": "SKID",
                    "description": "A description of my skid",
                    "imperial_weight": 200,
                    "weight_unit_value": "KGS",
                    "imperial_length": 48,
                    "imperial_width": 40,
                    "imperial_height": 40,
                    "unit_value": "cm",
                    "is_dangerous_good": False,
                },
                {
                    "class_value": "70.00",
                    "quantity": 2,
                    "package_type": "BOX",
                    "description": "A description of my pallets",
                    "imperial_weight": 500,
                    "weight_unit_value": "KG",
                    "imperial_length": 50,
                    "imperial_width": 60,
                    "imperial_height": 20,
                    "unit_value": "CM",
                    "is_dangerous_good": False,
                },
            ],
            "other": {
                "rock_solid_service_guarantee": True,
                "rock_solid_service_value": "A",
                "call_prior_to_delivery": False,
                "off_hour_pickup": False,
                "off_hour_delivery": False,
                "delivery_by_appointment": False,
                "reference_one": "test ref",
            },
            "special_instructions": "test instructions",
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    MANITOULIN: {"account": carrier_account, "carrier": carrier},
                },
            },
            "carrier_options": [],
            "service_code": "LTL|LF3Q761752",
            "order_number": "UB1234567890",
        }

        self._manitoulin_transit = ManitoulinTransitTime(ubbe_request=self.request)

    def test_get_pickup_date(self):
        """
        Test pickup date
        """
        ret = self._manitoulin_transit._get_pickup_date()
        expected = "2021-08-12"
        self.assertEqual(expected, ret)

    def test_build_transit_request(self):
        """
        Test build request - LTL
        """
        ret = self._manitoulin_transit._build_transit_request()
        expected = {
            "origin_city": "Edmonton International Airport",
            "origin_province": "ON",
            "destination_city": "CALGARY",
            "destination_province": "AB",
            "pickup_date": "2021-08-12",
        }
        self.assertEqual(expected, ret)

    def test_build_transit_request_rock_solid(self):
        """
        Test build request - rock solid guarantee service
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "ROCKA|LF3Q761752"
        manitoulin_transit = ManitoulinTransitTime(ubbe_request=copied)
        ret = manitoulin_transit._build_transit_request()
        expected = {
            "origin_city": "Edmonton International Airport",
            "origin_province": "ON",
            "destination_city": "CALGARY",
            "destination_province": "AB",
            "pickup_date": "2021-08-12",
            "guaranteed_service": True,
            "guaranteed_service_option": "A",
        }
        self.assertEqual(expected, ret)
