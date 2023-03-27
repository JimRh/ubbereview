"""
    Title: Purolator Service Unit Tests
    Description: Unit Tests for the Purolator Service. Test Everything.
    Created: November 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.courier.endpoints.purolator_ship import PurolatorShip
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
                "ResponseContext": {
                    "ResponseReference": "CreateShipment - ub1234567890"
                }
            },
            "body": {
                "ResponseInformation": {
                    "Errors": None,
                    "InformationalMessages": {"InformationalMessage": []},
                },
                "ShipmentPIN": {"Value": "329026672488"},
                "PiecePINs": {"PIN": [{"Value": "329026672488"}]},
                "ReturnShipmentPINs": None,
                "ExpressChequePIN": {"Value": None},
            },
        }

        self._puro_ship = PurolatorShip(ubbe_request=self.request)
