"""
    Title: TwoShip Pickup Unit Tests
    Description: Unit Tests for the TwoShip Pickup. Test Everything.
    Created: January 23, 2023
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.twoship.endpoints.twoship_pickup_v2 import TwoShipPickup
from api.globals.carriers import UPS
from api.models import SubAccount, Carrier, CarrierAccount


class TwoShipPickupTests(TestCase):
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
            "carrier_id": UPS,
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
                    "length": Decimal("48"),
                    "width": Decimal("48"),
                    "height": Decimal("48"),
                    "weight": Decimal("100"),
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
            "service_name": "Express",
            "order_number": "UB1234567890",
            "is_metric": True,
            "special_instructions": "test test test",
        }

        self._two_pickup = TwoShipPickup(ubbe_request=self.request)

    def test_get_package_totals(self):
        """
        Test TwoShip get package totals
        :return:
        """

        total_quantity, total_weight = self._two_pickup._get_package_totals()
        expected_total_quantity = 1
        expected_total_weight = Decimal("100")

        self.assertEqual(expected_total_quantity, total_quantity)
        self.assertEqual(expected_total_weight, total_weight)

    def test_build_request_express(self):
        """
        Test TwoShip Pickup Request
        :return:
        """

        ret = self._two_pickup._build_request()
        del ret["WS_Key"]
        expected = {
            "LocationID": 4110,
            "CarrierId": 8,
            "PickupDate": "2023-01-23",
            "ReadyTime": "10:00",
            "CompanyCloseTime": "16:00",
            "PickupDescription": "test test test",
            "PickupAddress": {
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
            },
            "ShipmentData": {
                "DestinationCountry": "CA",
                "MeasurementsType": 1,
                "ServiceType": 0,
                "ServiceCode": "STD",
                "NumberOfPackage": 1,
                "TotalWeight": Decimal("100.00"),
            },
        }

        self.assertDictEqual(expected, ret)

    def test_build_request_ground(self):
        """
        Test TwoShip Pickup Request
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["service_name"] = "Ground"

        two_pickup = TwoShipPickup(ubbe_request=copied)
        ret = two_pickup._build_request()
        del ret["WS_Key"]
        expected = {
            "LocationID": 4110,
            "CarrierId": 8,
            "PickupDate": "2023-01-23",
            "ReadyTime": "10:00",
            "CompanyCloseTime": "16:00",
            "PickupDescription": "test test test",
            "PickupAddress": {
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
            },
            "ShipmentData": {
                "DestinationCountry": "CA",
                "MeasurementsType": 1,
                "ServiceType": 1,
                "ServiceCode": "STD",
                "NumberOfPackage": 1,
                "TotalWeight": Decimal("100.00"),
            },
        }

        self.assertDictEqual(expected, ret)

    def test_build_request_imperial(self):
        """
        Test TwoShip Pickup Request
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["is_metric"] = False

        two_pickup = TwoShipPickup(ubbe_request=copied)
        ret = two_pickup._build_request()
        del ret["WS_Key"]
        expected = {
            "LocationID": 4110,
            "CarrierId": 8,
            "PickupDate": "2023-01-23",
            "ReadyTime": "10:00",
            "CompanyCloseTime": "16:00",
            "PickupDescription": "test test test",
            "PickupAddress": {
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
            },
            "ShipmentData": {
                "DestinationCountry": "CA",
                "MeasurementsType": 0,
                "ServiceType": 0,
                "ServiceCode": "STD",
                "NumberOfPackage": 1,
                "TotalWeight": Decimal("100.00"),
            },
        }

        self.assertDictEqual(expected, ret)
