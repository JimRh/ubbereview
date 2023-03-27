"""
    Title: Purolator Address Helper Unit Tests
    Description: Unit Tests for the Purolator Address Helpers. Test Everything.
    Created: November 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.helpers.address import PurolatorAddress
from api.models import CarrierAccount, Carrier, SubAccount


class PurolatorAddressTests(TestCase):
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

        self.request_rate = {
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
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    11: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self._puro_address_rate = PurolatorAddress(
            is_rate=True, ubbe_request=self.request_rate
        )
        self._puro_address_ship = PurolatorAddress(
            is_rate=False, ubbe_request=self.request_rate
        )

    def test_get_street_info(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="8812 218 street nw"
        )
        self.assertEqual("8812", number)
        self.assertEqual("Street", street_type)

    def test_get_street_info_two(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="Industrial Park Michael Street 1621"
        )
        self.assertEqual("1621", number)
        self.assertEqual("Street", street_type)

    def test_get_street_info_three(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="1759-35 avenue east"
        )
        self.assertEqual("1759", number)
        self.assertEqual("Avenue", street_type)

    def test_get_street_info_four(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="1759 35 avenue east"
        )
        self.assertEqual("1759", number)
        self.assertEqual("Avenue", street_type)

    def test_get_street_info_five(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="1759 35 avenue E"
        )
        self.assertEqual("1759", number)
        self.assertEqual("Avenue", street_type)

    def test_get_street_info_six(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="10030 114 Street NW"
        )
        self.assertEqual("10030", number)
        self.assertEqual("Street", street_type)

    def test_get_street_info_seven(self):
        number, street_type = self._puro_address_rate._get_street_info(
            address="1540 Airport Road"
        )
        self.assertEqual("1540", number)
        self.assertEqual("Road", street_type)

    def test_address_origin(self):
        address = self._puro_address_rate.address(address=self.request_rate["origin"])

        expected = {
            "Name": "Kenneth Carmichael",
            "Company": "BBE Ottawa",
            "StreetNumber": "1540",
            "StreetName": "Airport Road",
            "StreetType": "Road",
            "StreetAddress2": "",
            "City": "Edmonton International Airport",
            "Province": "AB",
            "Country": "CA",
            "PostalCode": "T9E0V6",
        }

        self.assertDictEqual(expected, address)

    def test_address_destination(self):
        address = self._puro_address_rate.address(
            address=self.request_rate["destination"]
        )

        expected = {
            "Name": "Kenneth Carhael",
            "Company": "BBE Ottawa",
            "StreetNumber": "1540",
            "StreetName": "Airport Road",
            "StreetType": "Road",
            "StreetAddress2": "",
            "City": "Edmonton",
            "Province": "AB",
            "Country": "CA",
            "PostalCode": "T5T4R7",
        }

        self.assertDictEqual(expected, address)

    def test_address_origin_ship(self):
        address = self._puro_address_ship.address(address=self.request_rate["origin"])

        expected = {
            "Name": "Kenneth Carmichael",
            "Company": "BBE Ottawa",
            "StreetNumber": "1540",
            "StreetName": "Airport Road",
            "StreetType": "Road",
            "StreetAddress2": "",
            "City": "Edmonton International Airport",
            "Province": "AB",
            "Country": "CA",
            "PostalCode": "T9E0V6",
            "PhoneNumber": {
                "CountryCode": 1,
                "AreaCode": "780",
                "Phone": "9326245",
                "Extension": "",
            },
        }

        self.assertDictEqual(expected, address)

    def test_address_destination_ship(self):
        address = self._puro_address_ship.address(
            address=self.request_rate["destination"]
        )

        expected = {
            "Name": "Kenneth Carhael",
            "Company": "BBE Ottawa",
            "StreetNumber": "1540",
            "StreetName": "Airport Road",
            "StreetType": "Road",
            "StreetAddress2": "",
            "City": "Edmonton",
            "Province": "AB",
            "Country": "CA",
            "PostalCode": "T5T4R7",
            "PhoneNumber": {
                "CountryCode": 1,
                "AreaCode": "780",
                "Phone": "8908614",
                "Extension": "",
            },
        }

        self.assertDictEqual(expected, address)
