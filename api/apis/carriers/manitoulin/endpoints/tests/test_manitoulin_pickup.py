"""
    Title: Manitoulin Pickup Unit Tests
    Description: Unit Tests for the Manitoulin Pickup. Test Everything.
    Created: January 09, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.manitoulin.endpoints.manitoulin_pickup import ManitoulinPickup
from api.globals.carriers import MANITOULIN
from api.models import SubAccount, Carrier, CarrierAccount, API


class ManiotulinPickupTests(TestCase):
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
        #

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "postal_code": "T9E0V6",
                "province": "AB",
                "country": "CA",
                "company_name": "BBE Ottawa",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "name": "BBE",
                "has_shipping_bays": True,
                "is_residential": False,
            },
            ""
            "destination": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "city": "Ottawa",
                "company_name": "BBE Ottawa",
                "name": "BBE",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "country": "CA",
                "postal_code": "K1V0R1",
                "province": "ON",
                "has_shipping_bays": True,
                "is_residential": False,
            },
            "pickup": {
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "packages": [
                {
                    "freight_class": "70.00",
                    "quantity": 1,
                    "package_type": "SKID",
                    "description": "A description of my skid",
                    "imperial_weight": Decimal("200"),
                    "weight_unit_value": "KGS",
                    "imperial_length": Decimal("48"),
                    "imperial_width": Decimal("40"),
                    "imperial_height": Decimal("40"),
                    "unit_value": "cm",
                },
                {
                    "freight_class": "70.00",
                    "quantity": 2,
                    "package_type": "BOX",
                    "description": "A description of my pallets",
                    "imperial_weight": Decimal("500"),
                    "weight_unit_value": "KG",
                    "imperial_length": Decimal("50"),
                    "imperial_width": Decimal("60"),
                    "imperial_height": Decimal("20"),
                    "unit_value": "CM",
                },
            ],
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

        self._manitoulin_pickup = ManitoulinPickup(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test build address origin.
        """
        ret = self._manitoulin_pickup._build_address(
            address=self.request["origin"], is_shipper=True
        )
        expected = {
            "address": "1540 Airport Road",
            "address_2": "1540 Airport Road",
            "city": "edmonton international airport",
            "postal": "T9E0V6",
            "province": "AB",
            "company": "BBE Ottawa",
            "contact": "BBE",
            "phone": "7809326245",
            "email": "developer@bbex.com",
            "private_residence": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test build address destination.
        """
        ret = self._manitoulin_pickup._build_address(
            address=self.request["destination"]
        )
        expected = {
            "address": "140 THAD JOHNSON PRIV Suite 7",
            "address_2": "140 THAD JOHNSON PRIV Suite 7",
            "city": "ottawa",
            "postal": "K1V0R1",
            "province": "ON",
            "company": "BBE Ottawa",
            "contact": "BBE",
            "phone": "7809326245",
            "email": "developer@bbex.com",
        }
        self.assertDictEqual(expected, ret)

    def test_build_third_party(self):
        ret = self._manitoulin_pickup._build_third_party()
        expected = {
            "company": "BBE Expediting LTD",
            "contact": "Customer Service",
            "phone": "8884206926",
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages(self):
        """
        Test build packages.
        """
        ret = self._manitoulin_pickup._build_packages()
        expected = (
            [
                {
                    "item_class": "70",
                    "package_code": "SKIDS",
                    "pieces": 1,
                    "weight": 200,
                    "length": 48,
                    "height": 40,
                    "width": 40,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
                {
                    "item_class": "70",
                    "package_code": "BOXES",
                    "pieces": 2,
                    "weight": 500,
                    "length": 50,
                    "height": 20,
                    "width": 60,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
            ],
            "A description of my skid, A description of my pallets, ",
        )

        self.assertEqual(expected, ret)

    def test_build_packages_multiple(self):
        """
        Test build packages - Multiple.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "Test",
                "package_type": "SKID",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100"),
                "is_dangerous_good": False,
            }
        )
        manitoulin_pickup = ManitoulinPickup(ubbe_request=copied)
        ret = manitoulin_pickup._build_packages()
        expected = (
            [
                {
                    "item_class": "70",
                    "package_code": "SKIDS",
                    "pieces": 1,
                    "weight": 200,
                    "length": 48,
                    "height": 40,
                    "width": 40,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
                {
                    "item_class": "70",
                    "package_code": "BOXES",
                    "pieces": 2,
                    "weight": 500,
                    "length": 50,
                    "height": 20,
                    "width": 60,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
                {
                    "item_class": "70",
                    "package_code": "SKIDS",
                    "pieces": 1,
                    "weight": 100,
                    "length": 48,
                    "height": 48,
                    "width": 48,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
            ],
            "A description of my skid, A description of my pallets, Test, ",
        )

        self.assertEqual(expected, ret)

    def test_build_packages_dg(self):
        """
        Test build packages - DG.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"] = [
            {
                "description": "TEST",
                "package_type": "DRUM",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100"),
                "is_dangerous_good": True,
                "proper_shipping_name": "My DG",
                "un_number": 1234,
                "class_div": "1",
                "packing_group_str": "III",
                "is_nos": False,
                "is_neq": False,
            }
        ]
        manitoulin_pickup = ManitoulinPickup(ubbe_request=copied)
        ret = manitoulin_pickup._build_packages()
        expected = (
            [
                {
                    "item_class": "70",
                    "package_code": "DRUMS",
                    "pieces": 1,
                    "weight": 100,
                    "length": 48,
                    "height": 48,
                    "width": 48,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                }
            ],
            "TEST, ",
        )

        self.assertEqual(expected, ret)

    def test_build_pickup(self):
        """
        Test build pickup.
        """
        ret = self._manitoulin_pickup._build_pickup()
        expected = {
            "pickup_date": "2021-08-12",
            "ready_time": "10:00",
            "closing_time": "16:00",
        }

        self.assertDictEqual(expected, ret)

    def test_build_pickup_no_pickup(self):
        """
        Test build pickup - no pickup in ubbe request.
        """
        today = datetime.datetime.today().date()
        copied = copy.deepcopy(self.request)
        del copied["pickup"]

        now = datetime.datetime.now()

        manitoulin_pickup = ManitoulinPickup(ubbe_request=copied)
        ret = manitoulin_pickup._build_pickup()
        expected = {
            "pickup_date": datetime.datetime.today().strftime("%Y-%m-%d"),
            "ready_time": "09:00",
            "closing_time": "18:00",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request(self):
        """
        Test build request.
        """
        ret = self._manitoulin_pickup._build_request()
        expected = {
            "requester": "Third Party",
            "shipper": {
                "address": "1540 Airport Road",
                "address_2": "1540 Airport Road",
                "city": "edmonton international airport",
                "postal": "T9E0V6",
                "province": "AB",
                "company": "BBE Ottawa",
                "contact": "BBE",
                "phone": "7809326245",
                "email": "developer@bbex.com",
                "private_residence": False,
            },
            "consignee": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "address_2": "140 THAD JOHNSON PRIV Suite 7",
                "city": "ottawa",
                "postal": "K1V0R1",
                "province": "ON",
                "company": "BBE Ottawa",
                "contact": "BBE",
                "phone": "7809326245",
                "email": "developer@bbex.com",
            },
            "items": [
                {
                    "item_class": "70",
                    "package_code": "SKIDS",
                    "pieces": 1,
                    "weight": 200,
                    "length": 48,
                    "height": 40,
                    "width": 40,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
                {
                    "item_class": "70",
                    "package_code": "BOXES",
                    "pieces": 2,
                    "weight": 500,
                    "length": 50,
                    "height": 20,
                    "width": 60,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
            ],
            "description": "A description of my ",
            "special_pickup_instruction": "test instructions",
            "special_delivery_instruction": "test instructions",
            "freight_charge_party": "Third Party Prepaid",
            "third_party": {
                "company": "BBE Expediting LTD",
                "contact": "Customer Service",
                "phone": "8884206926",
            },
            "confirm_pickup_receipt": True,
            "recipient": {
                "company": "BBE Expediting Ltd",
                "contact": "Customer Service",
                "email": "customerservice@ubbe.com",
                "contact_by": "Email",
                "pickup_confirmation": True,
            },
            "pickup_date": "2021-08-12",
            "ready_time": "10:00",
            "closing_time": "16:00",
        }

        self.assertDictEqual(expected, ret)

    def test_build_request_dg(self):
        """
        Test build request - dg.
        """

        copied = copy.deepcopy(self.request)
        copied["packages"] = [
            {
                "description": "TEST",
                "package_type": "DRUM",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100"),
                "is_dangerous_good": True,
                "proper_shipping_name": "My DG",
                "un_number": 1234,
                "class_div": "1",
                "packing_group_str": "III",
                "is_nos": False,
                "is_neq": False,
            }
        ]

        manitoulin_pickup = ManitoulinPickup(ubbe_request=copied)
        ret = manitoulin_pickup._build_request()

        expected = {
            "requester": "Third Party",
            "shipper": {
                "address": "1540 Airport Road",
                "address_2": "1540 Airport Road",
                "city": "edmonton international airport",
                "postal": "T9E0V6",
                "province": "AB",
                "company": "BBE Ottawa",
                "contact": "BBE",
                "phone": "7809326245",
                "email": "developer@bbex.com",
                "private_residence": False,
            },
            "consignee": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "address_2": "140 THAD JOHNSON PRIV Suite 7",
                "city": "ottawa",
                "postal": "K1V0R1",
                "province": "ON",
                "company": "BBE Ottawa",
                "contact": "BBE",
                "phone": "7809326245",
                "email": "developer@bbex.com",
            },
            "items": [
                {
                    "item_class": "70",
                    "package_code": "DRUMS",
                    "pieces": 1,
                    "weight": 100,
                    "length": 48,
                    "height": 48,
                    "width": 48,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                }
            ],
            "description": "TEST, ",
            "special_pickup_instruction": "test instructions",
            "special_delivery_instruction": "test instructions",
            "freight_charge_party": "Third Party Prepaid",
            "third_party": {
                "company": "BBE Expediting LTD",
                "contact": "Customer Service",
                "phone": "8884206926",
            },
            "confirm_pickup_receipt": True,
            "recipient": {
                "company": "BBE Expediting Ltd",
                "contact": "Customer Service",
                "email": "customerservice@ubbe.com",
                "contact_by": "Email",
                "pickup_confirmation": True,
            },
            "pickup_date": "2021-08-12",
            "ready_time": "10:00",
            "closing_time": "16:00",
        }

        self.assertDictEqual(expected, ret)

    def test_build_request_rock_solid(self):
        """
        Test build request - rock solid guarantee service.
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "ROCKA|LF3Q761752"

        manitoulin_pickup = ManitoulinPickup(ubbe_request=copied)
        ret = manitoulin_pickup._build_request()
        expected = {
            "requester": "Third Party",
            "shipper": {
                "address": "1540 Airport Road",
                "address_2": "1540 Airport Road",
                "city": "edmonton international airport",
                "postal": "T9E0V6",
                "province": "AB",
                "company": "BBE Ottawa",
                "contact": "BBE",
                "phone": "7809326245",
                "email": "developer@bbex.com",
                "private_residence": False,
            },
            "consignee": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "address_2": "140 THAD JOHNSON PRIV Suite 7",
                "city": "ottawa",
                "postal": "K1V0R1",
                "province": "ON",
                "company": "BBE Ottawa",
                "contact": "BBE",
                "phone": "7809326245",
                "email": "developer@bbex.com",
            },
            "items": [
                {
                    "item_class": "70",
                    "package_code": "SKIDS",
                    "pieces": 1,
                    "weight": 200,
                    "length": 48,
                    "height": 40,
                    "width": 40,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
                {
                    "item_class": "70",
                    "package_code": "BOXES",
                    "pieces": 2,
                    "weight": 500,
                    "length": 50,
                    "height": 20,
                    "width": 60,
                    "weight_units": "LBS",
                    "dimension_units": "IN",
                },
            ],
            "description": "A description of my ",
            "special_pickup_instruction": "test instructions",
            "special_delivery_instruction": "test instructions",
            "freight_charge_party": "Third Party Prepaid",
            "third_party": {
                "company": "BBE Expediting LTD",
                "contact": "Customer Service",
                "phone": "8884206926",
            },
            "confirm_pickup_receipt": True,
            "recipient": {
                "company": "BBE Expediting Ltd",
                "contact": "Customer Service",
                "email": "customerservice@ubbe.com",
                "contact_by": "Email",
                "pickup_confirmation": True,
            },
            "pickup_date": "2021-08-12",
            "ready_time": "10:00",
            "closing_time": "16:00",
            "guaranteed_service": True,
            "guaranteed_option": "By noon",
        }

        self.assertDictEqual(expected, ret)

    def test_format_response(self):
        """
        Test Format Response for Manitoulin
        """
        response = {"punum": "0000001"}

        ret = self._manitoulin_pickup._format_response(response=response)
        expected = {
            "pickup_id": "0000001",
            "pickup_message": "Success",
            "pickup_status": "Booked",
        }

        self.assertDictEqual(expected, ret)

    def test_format_response_empty(self):
        """
        Test Format Response for Manitoulin
        """

        ret = self._manitoulin_pickup._format_response(response={})
        expected = {
            "pickup_id": "",
            "pickup_message": "(Manitoulin) Pickup Failed.",
            "pickup_status": "Failed",
        }
        self.assertDictEqual(expected, ret)
