"""
    Title: YRC Rate Unit Tests
    Description: Unit Tests for the YRC Rate. Test Everything.
    Created: January 18, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.yrc.endpoints.yrc_pickup import YRCPickup
from api.apis.carriers.yrc.endpoints.yrc_rate import YRCRate
from api.globals.carriers import YRC
from api.models import SubAccount, Carrier, CarrierAccount


class YRCPickupTests(TestCase):
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
        carrier = Carrier.objects.get(code=YRC)
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
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date(),
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
                    YRC: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
            "service_code": "STD",
            "order_number": "UB1234567890",
        }

        self.response_one = {
            "isSuccess": True,
            "referenceIds": ["87380070"],
            "createTS": "2017-07-14T11:58:06-05:00",
            "isWeatherAlert": False,
            "isDirect": True,
        }
        self.response_two = {
            "isSuccess": True,
            "masterId": "87388888",
            "referenceIds": ["87380070", "87380070"],
            "createTS": "2017-07-14T11:58:06-05:00",
            "isWeatherAlert": False,
            "isDirect": True,
        }

        self._yrc_pickup = YRCPickup(ubbe_request=self.request)

    def test_build_third_party(self):
        """
        Test Pickup Building of third party.
        """
        ret = self._yrc_pickup._build_third_party()
        expected = {
            "role": "Third Party",
            "company": "BBE Expediting LTD",
            "address": "1759-35 Ave E",
            "city": "Edmonton Intl Airport",
            "state": "AB",
            "postalCode": "T9E0V6",
            "country": "CAN",
            "contact": {
                "name": "Customer Service",
                "email": "customerservice@ubbe.com",
                "phone": "888-420-6926",
            },
        }
        self.assertDictEqual(expected, ret)

    def test_build_destination(self):
        """
        Test Pickup Building of destination.
        """
        ret = self._yrc_pickup._build_destination()
        expected = {
            "company": "BBE Ottawa",
            "address": "140 THAD JOHNSON PRIV Suite 7",
            "city": "ottawa",
            "state": "ON",
            "postalCode": "K1V0R1",
            "country": "CAN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_location(self):
        """
        Test Pickup Building of location in ca.
        """
        ret = self._yrc_pickup._build_location(address=self.request["origin"])
        expected = {
            "company": "BBE Ottawa",
            "address": "1540 Airport Road",
            "city": "edmonton international airport",
            "state": "AB",
            "postalCode": "T9E0V6",
            "country": "CAN",
            "contact": {
                "name": "BBE",
                "email": "developer@bbex.com",
                "phone": "7809326245",
            },
        }
        self.assertDictEqual(expected, ret)

    def test_build_location_usa(self):
        """
        Test Pickup Building of location in us.
        """
        copied = copy.deepcopy(self.request)
        copied["origin"] = {
            "address": "452 Morse Road",
            "city": "Bennington",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "US",
            "postal_code": "05201",
            "province": "VT",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = self._yrc_pickup._build_location(address=copied["origin"])
        expected = {
            "company": "BBE Ottawa",
            "address": "452 Morse Road",
            "city": "bennington",
            "state": "VT",
            "postalCode": "05201",
            "country": "USA",
            "contact": {
                "name": "BBE",
                "email": "developer@bbex.com",
                "phone": "7809326245",
            },
        }
        self.assertDictEqual(expected, ret)

    def test_build_location_mexico(self):
        """
        Test Pickup Building of location is mexico.
        """
        copied = copy.deepcopy(self.request)
        copied["origin"] = {
            "address": "Predio Paraiso Escondido s/n",
            "city": "Cabo San Lucas",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "MX",
            "postal_code": "23450",
            "province": "BCS",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = self._yrc_pickup._build_location(address=copied["origin"])
        expected = {
            "company": "BBE Ottawa",
            "address": "Predio Paraiso Escondido s/n",
            "city": "cabo san lucas",
            "state": "BCS",
            "postalCode": "23450",
            "country": "MEX",
            "contact": {
                "name": "BBE",
                "email": "developer@bbex.com",
                "phone": "7809326245",
            },
        }
        self.assertDictEqual(expected, ret)

    def test_build_login(self):
        """
        Test Pickup Building of login.
        """
        ret = self._yrc_pickup._build_login()
        expected = {"username": "BBEYZF", "password": "BBEYZF"}
        self.assertDictEqual(expected, ret)

    def test_build_shipments(self):
        """
        Test Pickup Building of login.
        """
        destination = self._yrc_pickup._build_destination()
        ret = self._yrc_pickup._build_shipments(destination=destination)
        expected = [
            {
                "destination": {
                    "company": "BBE Ottawa",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "postalCode": "K1V0R1",
                    "country": "CAN",
                },
                "pieces": 1,
                "pieceType": "PLT",
                "weightLbs": 100,
                "length": 48,
                "width": 48,
                "height": 48,
                "service": "LTL",
                "paymentTerms": "PPD",
                "isFood": False,
                "isPoison": False,
                "isCertified": False,
                "isHazardous": False,
                "isFreezable": False,
                "isEmailConfirmation": False,
                "trackingType": "PO",
                "trackingNumber": "UB1234567890",
            }
        ]
        self.assertListEqual(expected, ret)

    def test_build_shipments_drum(self):
        """
        Test Pickup Building of login.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
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
                "is_dangerous_good": False,
            }
        )

        destination = self._yrc_pickup._build_destination()
        ret = YRCPickup(ubbe_request=copied)._build_shipments(destination=destination)
        expected = [
            {
                "destination": {
                    "company": "BBE Ottawa",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "postalCode": "K1V0R1",
                    "country": "CAN",
                },
                "pieces": 1,
                "pieceType": "PLT",
                "weightLbs": 100,
                "length": 48,
                "width": 48,
                "height": 48,
                "service": "LTL",
                "paymentTerms": "PPD",
                "isFood": False,
                "isPoison": False,
                "isCertified": False,
                "isHazardous": False,
                "isFreezable": False,
                "isEmailConfirmation": False,
                "trackingType": "PO",
                "trackingNumber": "UB1234567890",
            },
            {
                "destination": {
                    "company": "BBE Ottawa",
                    "address": "140 THAD JOHNSON PRIV Suite 7",
                    "city": "ottawa",
                    "state": "ON",
                    "postalCode": "K1V0R1",
                    "country": "CAN",
                },
                "pieces": 1,
                "pieceType": "DRM",
                "weightLbs": 100,
                "length": 48,
                "width": 48,
                "height": 48,
                "service": "LTL",
                "paymentTerms": "PPD",
                "isFood": False,
                "isPoison": False,
                "isCertified": False,
                "isHazardous": False,
                "isFreezable": False,
                "isEmailConfirmation": False,
                "trackingType": "PO",
                "trackingNumber": "UB1234567890",
            },
        ]
        self.assertListEqual(expected, ret)

    def test_create_request(self):
        """
        Test Pickup Building of login.
        """
        ret = self._yrc_pickup._create_request()
        expected = {
            "login": {"username": "BBEYZF", "password": "BBEYZF"},
            "requester": {
                "role": "Third Party",
                "company": "BBE Expediting LTD",
                "address": "1759-35 Ave E",
                "city": "Edmonton Intl Airport",
                "state": "AB",
                "postalCode": "T9E0V6",
                "country": "CAN",
                "contact": {
                    "name": "Customer Service",
                    "email": "customerservice@ubbe.com",
                    "phone": "888-420-6926",
                },
            },
            "pickupLocation": {
                "company": "BBE Ottawa",
                "address": "1540 Airport Road",
                "city": "edmonton international airport",
                "state": "AB",
                "postalCode": "T9E0V6",
                "country": "CAN",
                "contact": {
                    "name": "BBE",
                    "email": "developer@bbex.com",
                    "phone": "7809326245",
                },
            },
            "pickupDate": "08/12/2021",
            "readyTime": "10:00",
            "closeTime": "16:00",
            "isLiftgate": False,
            "pickupNotes": "",
            "shipments": [
                {
                    "destination": {
                        "company": "BBE Ottawa",
                        "address": "140 THAD JOHNSON PRIV Suite 7",
                        "city": "ottawa",
                        "state": "ON",
                        "postalCode": "K1V0R1",
                        "country": "CAN",
                    },
                    "pieces": 1,
                    "pieceType": "PLT",
                    "weightLbs": 100,
                    "length": 48,
                    "width": 48,
                    "height": 48,
                    "service": "LTL",
                    "paymentTerms": "PPD",
                    "isFood": False,
                    "isPoison": False,
                    "isCertified": False,
                    "isHazardous": False,
                    "isFreezable": False,
                    "isEmailConfirmation": False,
                    "trackingType": "PO",
                    "trackingNumber": "UB1234567890",
                }
            ],
        }
        self.assertDictEqual(expected, ret)

    def test_format_response_one(self):
        """
        Test Pickup formatting pickup response.
        """
        self._yrc_pickup._format_response(response=self.response_one)
        expected = {'pickup_id': '87380070', 'pickup_message': 'Booked', 'pickup_status': 'Success', 'is_direct': True, 'is_weather': False}
        self.assertDictEqual(expected, self._yrc_pickup._response)

    def test_format_response_two(self):
        """
        Test Pickup formatting pickup response with master id.
        """
        self._yrc_pickup._format_response(response=self.response_two)
        expected = {'pickup_id': '87388888', 'pickup_message': 'Booked', 'pickup_status': 'Success', 'is_direct': True, 'is_weather': False}
        self.assertDictEqual(expected, self._yrc_pickup._response)
