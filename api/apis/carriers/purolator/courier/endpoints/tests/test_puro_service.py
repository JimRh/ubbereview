"""
    Title: Purolator Service Unit Tests
    Description: Unit Tests for the Purolator Service. Test Everything.
    Created: November 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.courier.endpoints.purolator_service import (
    PurolatorService,
)
from api.models import SubAccount, Carrier, CarrierAccount


class PurolatorServiceTests(TestCase):
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
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
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

        self.response = {
            "header": {
                "ResponseContext": {"ResponseReference": "ValidateCityPostalCodeZip"}
            },
            "body": {
                "ResponseInformation": {
                    "Errors": None,
                    "InformationalMessages": {"InformationalMessage": []},
                },
                "SuggestedAddresses": {
                    "SuggestedAddress": [
                        {
                            "Address": {
                                "City": "Edmonton International Airport",
                                "Province": "AB",
                                "Country": "CA",
                                "PostalCode": "T9E0V6",
                            },
                            "ResponseInformation": {
                                "Errors": None,
                                "InformationalMessages": {"InformationalMessage": []},
                            },
                        }
                    ]
                },
            },
        }

        self._puro_service = PurolatorService(ubbe_request=self.request)

    def test_short_address_origin(self):
        address = self._puro_service._short_address(address=self.request["origin"])
        expected = {
            "City": "Edmonton International Airport",
            "Province": "AB",
            "Country": "CA",
            "PostalCode": "T9E0V6",
        }
        self.assertDictEqual(expected, address)

    def test_short_address_destination(self):
        address = self._puro_service._short_address(address=self.request["destination"])
        expected = {
            "City": "Edmonton",
            "Province": "AB",
            "Country": "CA",
            "PostalCode": "T5T4R7",
        }
        self.assertDictEqual(expected, address)

    def test_formant_validate(self):
        address = self._puro_service._formant_validate(response=self.response)
        expected = {
            "city": "Edmonton International Airport",
            "province": "AB",
            "country": "CA",
            "postal_code": "T9E0V6",
        }
        self.assertDictEqual(expected, address)

    def test_formant_validate_bad(self):
        copied = copy.deepcopy(self.response)
        copied["body"]["SuggestedAddresses"]["SuggestedAddress"].pop()
        address = self._puro_service._formant_validate(response=copied)
        expected = {}
        self.assertDictEqual(expected, address)
