"""
    Title: TwoShip Base Unit Tests
    Description: Unit Tests for the TwoShip Base. Test Everything.
    Created: January 23, 2023
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.twoship.endpoints.twoship_base_v2 import TwoShipBase
from api.globals.carriers import UPS
from api.models import SubAccount, Carrier, CarrierAccount


class TwoShipBaseTests(TestCase):
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
        sub_account = SubAccount.objects.get(is_default=True)
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=UPS)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "name": "BBE",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "is_residential": False,
                "has_shipping_bays": True,
            },
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
                "date": datetime.datetime.strptime("2023-01-23", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "packages": [
                {
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
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    UPS: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
            "service_code": "STD",
            "order_number": "UB1234567890",
        }

        self._two_base = TwoShipBase(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test TwoShip address building for origin
        :return:
        """

        ret = self._two_base._build_address(
            address=self.request["origin"], carrier_id=UPS
        )
        expected = {
            "Address1": "1540 Airport Road",
            "Address2": "",
            "City": "edmonton international airport",
            "CompanyName": "BBE Ottawa",
            "Country": "CA",
            "Email": "customerservice@ubbe.com",
            "IsResidential": False,
            "PersonName": "BBE",
            "PostalCode": "T9E0V6",
            "State": "AB",
            "Telephone": "7809326245",
            "TelephoneExtension": "",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test TwoShip address building for destination
        :return:
        """

        ret = self._two_base._build_address(
            address=self.request["destination"], carrier_id=UPS
        )
        expected = {
            "Address1": "140 THAD JOHNSON PRIV Suite 7",
            "Address2": "",
            "City": "ottawa",
            "CompanyName": "BBE Ottawa",
            "Country": "CA",
            "Email": "customerservice@ubbe.com",
            "IsResidential": False,
            "PersonName": "BBE",
            "PostalCode": "K1V0R1",
            "State": "ON",
            "Telephone": "7809326245",
            "TelephoneExtension": "",
        }

        self.assertDictEqual(expected, ret)

    def test_get_total_of_key(self):
        """
        Test TwoShip getting total for key.
        :return:
        """
        taxes = [{"Name": "GST", "Percentage": 5.0, "Amount": 7.660}]

        ret = self._two_base._get_total_of_key(items=taxes, key="Amount")
        expected = Decimal("7.66")

        self.assertEqual(expected, ret)

    def test_get_total_of_key_two(self):
        """
        Test TwoShip getting total for key.
        :return:
        """
        taxes = [
            {"Name": "GST", "Percentage": 5.0, "Amount": 7.660},
            {"Name": "GST", "Percentage": 5.0, "Amount": 7.660},
            {"Name": "GST", "Percentage": 5.0, "Amount": 7.660},
        ]

        ret = self._two_base._get_total_of_key(items=taxes, key="Amount")
        expected = Decimal("22.98")

        self.assertEqual(expected, ret)
