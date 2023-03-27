"""
    Title: Manitoulin Rate Unit Tests
    Description: Unit Tests for the Manitoulin Rate. Test Everything.
    Created: December 23, 2022
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.manitoulin.endpoints.manitoulin_rate import ManitoulinRate
from api.apis.carriers.manitoulin.endpoints.manitoulin_base import ManitoulinBaseApi
from api.globals.carriers import MANITOULIN
from api.models import SubAccount, Carrier, CarrierAccount


class ManitoulinRateTests(TestCase):
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
            "pickup_date": "2023-01-05",
            "contact": {
                "name": "Example User",
                "company": "BBE EXPEDITING LTD",
                "contact_method": "E",
                "email": "example.user@mycompany.com",
                "shipment_type": "ROAD",
                "shipment_terms": "PPD",
            },
            "origin": {
                "city": "TORONTO",
                "province": "ON",
                "country": "CA",
                "postal_code": "M1B",
                "residential_pickup": False,
                "tailgate_pickup": False,
                "flat_deck_pickup": False,
                "inside_pickup": False,
                "drop_off_at_terminal": False,
                "warehouse_pickup": False,
            },
            "destination": {
                "city": "CALGARY",
                "province": "AB",
                "country": "CA",
                "postal_code": "T2A1A1",
                "residential_delivery": False,
                "tailgate_delivery": False,
                "flat_deck_delivery": False,
                "inside_delivery": False,
                "dock_pickup": False,
            },
            "packages": [
                {
                    "freight_class": "70.00",
                    "quantity": 1,
                    "package_type": "SKID",
                    "description": "A description of my skid",
                    "imperial_weight": Decimal("200"),
                    "weight_unit_value": "LBS",
                    "imperial_length": Decimal("48"),
                    "imperial_width": Decimal("40"),
                    "imperial_height": Decimal("40"),
                    "unit_value": "I",
                }
            ],
            "other": {
                "declared_value": 0,
                "currency_type": "C",
                "protective_services_heat": False,
                "protective_services_reefer": False,
                "rock_solid_service_guarantee": True,
                "rock_solid_service_value": "A",
                "call_prior_to_delivery": False,
                "off_hour_pickup": False,
                "off_hour_delivery": False,
                "delivery_by_appointment": False,
                "rural_route": False,
            },
            "carrier_options": [3, 9, 17, 10],
            "is_dangerous_goods": False,
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    MANITOULIN: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self._manitoulin_rate = ManitoulinRate(ubbe_request=self.request)

    def test_build_contact(self):
        """
        Test build contact.
        """

        ret = self._manitoulin_rate._build_contact()
        expected = {
            "name": "Customer Service",
            "company": "BBE EXPEDITING LTD",
            "contact_method": "E",
            "contact_method_value": "customerservice@ubbe.com",
            "shipment_type": "ROAD",
            "shipment_terms": ManitoulinBaseApi._payment_terms,
        }
        self.assertDictEqual(expected, ret)

    def test_build_rate_address_origin(self):
        """
        Test build address - origin.
        """
        ret = self._manitoulin_rate._build_rate_address(
            "origin", self.request["origin"]
        )
        expected = {
            "city": "toronto",
            "province": "ON",
            "postal_zip": "M1B",
            "residential_pickup": False,
            "inside_pickup": True,
            "tailgate_pickup": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_rate_address_destination(self):
        """
        Test build address - destination.
        """
        ret = self._manitoulin_rate._build_rate_address(
            "destination", self.request["destination"]
        )
        expected = {
            "city": "calgary",
            "province": "AB",
            "postal_zip": "T2A1A1",
            "residential_delivery": False,
            "inside_delivery": True,
            "tailgate_delivery": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_options(self):
        """
        Test build address options.
        """

        copied = copy.deepcopy(self.request)
        ret = self._manitoulin_rate._build_address_options("origin")
        expected = {
            "tailgate_pickup": False,
            "inside_pickup": True,
            "residential_pickup": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages(self):
        """
        Test build packages.
        """
        ret = self._manitoulin_rate._build_packages()
        expected = [
            {
                "class_value": "70",
                "pieces": 1,
                "description": "A description of my skid",
                "package_code_value": "SK",
                "total_weight": 200,
                "weight_unit_value": "LBS",
                "length": 48,
                "height": 40,
                "width": 40,
                "unit_value": "I",
            }
        ]

        self.assertEqual(expected, ret)

    def test_build_packages_multiple(self):
        """
        Test build multiple packages.
        """
        self.request["packages"].append(
            {
                "freight_class": "70.00",
                "quantity": 1,
                "package_type": "SKID",
                "description": "A description of my skid",
                "imperial_weight": Decimal("200"),
                "weight_unit_value": "LBS",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("40"),
                "imperial_height": Decimal("40"),
                "unit_value": "I",
            }
        )
        manitoulin_rate = ManitoulinRate(ubbe_request=self.request)
        ret = manitoulin_rate._build_packages()

        expected = [
            {
                "class_value": "70",
                "pieces": 1,
                "description": "A description of my skid",
                "package_code_value": "SK",
                "total_weight": 200,
                "weight_unit_value": "LBS",
                "length": 48,
                "height": 40,
                "width": 40,
                "unit_value": "I",
            },
            {
                "class_value": "70",
                "pieces": 1,
                "description": "A description of my skid",
                "package_code_value": "SK",
                "total_weight": 200,
                "weight_unit_value": "LBS",
                "length": 48,
                "height": 40,
                "width": 40,
                "unit_value": "I",
            },
        ]
        self.assertEqual(expected, ret)

    def test_build_other(self):
        """
        Test build other
        """

        manitoulin_rate = ManitoulinRate(ubbe_request=self.request)
        ret = manitoulin_rate._build_other()
        expected = {
            "currency_type": "C",
            "dangerous_goods": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_request(self):
        """
        Test build request
        """
        ret = self._manitoulin_rate._build_request()
        expected = {
            "contact": {
                "name": "Customer Service",
                "company": "BBE EXPEDITING LTD",
                "contact_method": "E",
                "contact_method_value": "customerservice@ubbe.com",
                "shipment_type": "ROAD",
                "shipment_terms": "PPD",
            },
            "origin": {
                "city": "toronto",
                "province": "ON",
                "postal_zip": "M1B",
                "tailgate_pickup": False,
                "inside_pickup": True,
                "residential_pickup": False,
            },
            "destination": {
                "city": "calgary",
                "province": "AB",
                "postal_zip": "T2A1A1",
                "tailgate_delivery": False,
                "inside_delivery": True,
                "residential_delivery": False,
            },
            "items": [
                {
                    "class_value": "70",
                    "pieces": 1,
                    "description": "A description of my skid",
                    "package_code_value": "SK",
                    "total_weight": 200,
                    "weight_unit_value": "LBS",
                    "length": 48,
                    "height": 40,
                    "width": 40,
                    "unit_value": "I",
                }
            ],
            "other": {"currency_type": "C", "dangerous_goods": False},
            "service_code": "LTL",
        }
        self.assertDictEqual(expected, ret)

    def test_format_response_empty(self):
        """
        Test Format Empty Response
        """
        manitoulin_rate = ManitoulinRate(ubbe_request=self.request)
        ret = manitoulin_rate._format_response(responses=[])
        expected = []

        self.assertListEqual(expected, ret)
