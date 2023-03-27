"""
    Title: Purolator Pickup Unit Tests
    Description: Unit Tests for the Purolator Pickup. Test Everything.
    Created: December 8, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.courier.helpers.shipment import PurolatorShipment
from api.apis.carriers.purolator.courier.endpoints.purolator_pickup import (
    PurolatorPickup,
)
from api.models import SubAccount, Carrier, CarrierAccount


class PurolatorPickupTests(TestCase):
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
        carrier = Carrier.objects.get(code=11)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "name": "Kenneth Carmichael",
                "phone": "7809326245",
                "email": "kcarmichael@bbex.com",
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
                "name": "Kenneth Carhael",
                "phone": "7808908614",
                "email": "kcarmichael@bbex.com",
            },
            "packages": [
                {
                    "quantity": 1,
                    "length": "100",
                    "width": "50",
                    "height": "50",
                    "weight": "50",
                    "package_type": "BOX",
                }
            ],
            "pickup": {
                "start_time": "15:30",
                "date": datetime.datetime.strptime("2020-12-08", "%Y-%m-%d").date(),
                "end_time": "18:00",
            },
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    11: {"account": carrier_account, "carrier": carrier}
                },
            },
            "order_number": "ub1234556789",
        }

        self.response = {
            "header": {
                "ResponseContext": {
                    "ResponseReference": "SchedulePickUp - ub1234567890"
                }
            },
            "body": {
                "ResponseInformation": {"Errors": None, "InformationalMessages": None},
                "PickUpConfirmationNumber": "00006293",
            },
        }

        self._puro_shipment = PurolatorShipment(
            is_rate=False, ubbe_request=self.request
        )
        self._puro_pickup = PurolatorPickup(ubbe_request=self.request)

    def test_build_pickup_instructions(self):
        expected = {
            "Date": "2020-12-08",
            "AnyTimeAfter": "15:30",
            "UntilTime": "18:00",
            "PickUpLocation": "FrontDesk",
        }

        pickup = self._puro_pickup._build_pickup_instructions()

        self.assertDictEqual(expected, pickup)

    def test_build_pickup_instructions_two(self):
        copied = copy.deepcopy(self.request)
        copied["pickup"] = {
            "start_time": "08:30",
            "date": datetime.datetime.strptime("2020-12-20", "%Y-%m-%d").date(),
            "end_time": "20:00",
        }
        puro_pickup = PurolatorPickup(ubbe_request=copied)

        expected = {
            "Date": "2020-12-20",
            "AnyTimeAfter": "08:30",
            "UntilTime": "20:00",
            "PickUpLocation": "FrontDesk",
        }

        pickup = puro_pickup._build_pickup_instructions()

        self.assertDictEqual(expected, pickup)

    def test_build_pickup_instructions_three(self):
        copied = copy.deepcopy(self.request)
        copied["pickup"] = {
            "start_time": "10:30",
            "date": datetime.datetime.strptime("2020-12-31", "%Y-%m-%d").date(),
            "end_time": "12:00",
        }
        puro_pickup = PurolatorPickup(ubbe_request=copied)

        expected = {
            "Date": "2020-12-31",
            "AnyTimeAfter": "10:30",
            "UntilTime": "12:00",
            "PickUpLocation": "FrontDesk",
        }

        pickup = puro_pickup._build_pickup_instructions()

        self.assertDictEqual(expected, pickup)

    def test_build_pickup_instructions_next_day(self):
        expected = {
            "Date": "2020-12-09",
            "AnyTimeAfter": "08:00",
            "UntilTime": "18:00",
            "PickUpLocation": "FrontDesk",
        }

        pickup = self._puro_pickup._build_pickup_instructions(is_next_day=True)

        self.assertDictEqual(expected, pickup)

    def test_build_pickup_instructions_next_day_two(self):
        copied = copy.deepcopy(self.request)
        copied["pickup"] = {
            "start_time": "10:30",
            "date": datetime.datetime.strptime("2021-07-09", "%Y-%m-%d").date(),
            "end_time": "12:00",
        }
        puro_pickup = PurolatorPickup(ubbe_request=copied)

        expected = {
            "Date": "2021-07-12",
            "AnyTimeAfter": "08:00",
            "UntilTime": "18:00",
            "PickUpLocation": "FrontDesk",
        }

        pickup = puro_pickup._build_pickup_instructions(is_next_day=True)

        self.assertDictEqual(expected, pickup)

    def test_build_ship_summary_ca(self):
        expected = [
            {
                "ShipmentSummaryDetails": {
                    "ShipmentSummaryDetail": {
                        "DestinationCode": "DOM",
                        "TotalPieces": Decimal("1"),
                        "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                    }
                }
            }
        ]
        request = self._puro_shipment.shipment(account_number="AADADADA")

        pickup = self._puro_pickup._build_ship_summary(request=request)

        self.assertListEqual(expected, pickup)

    def test_build_ship_summary_us(self):
        copied = copy.deepcopy(self.request)
        copied["destination"]["country"] = "US"
        puro_shipment = PurolatorShipment(is_rate=False, ubbe_request=copied)
        request = puro_shipment.shipment(account_number="AADADADA")

        expected = [
            {
                "ShipmentSummaryDetails": {
                    "ShipmentSummaryDetail": {
                        "DestinationCode": "USA",
                        "TotalPieces": Decimal("1"),
                        "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                    }
                }
            }
        ]

        pickup = self._puro_pickup._build_ship_summary(request=request)

        self.assertListEqual(expected, pickup)

    def test_build_ship_summary_int(self):
        copied = copy.deepcopy(self.request)
        copied["destination"]["country"] = "UK"
        copied["destination"]["phone"] = "+443333206000"
        puro_shipment = PurolatorShipment(is_rate=False, ubbe_request=copied)
        request = puro_shipment.shipment(account_number="AADADADA")

        expected = [
            {
                "ShipmentSummaryDetails": {
                    "ShipmentSummaryDetail": {
                        "DestinationCode": "INT",
                        "TotalPieces": Decimal("1"),
                        "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                    }
                }
            }
        ]

        pickup = self._puro_pickup._build_ship_summary(request=request)

        self.assertListEqual(expected, pickup)
