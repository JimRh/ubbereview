"""
    Title: TwoShip Track Unit Tests
    Description: Unit Tests for the TwoShip track. Test Everything.
    Created: January 23, 2023
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime

from lxml import etree

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_track_v2 import TstCfExpressTrack
from api.globals.carriers import TST
from api.models import SubAccount, Carrier, CarrierAccount, Leg


class TstCfExpressTrackTests(TestCase):
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
        "markup",
        "shipments",
        "legs",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(is_default=True)
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=TST)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )
        leg = Leg.objects.last()

        self.request = {
            "leg": leg,
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    TST: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self._track_response = {}

        self.tst_track = TstCfExpressTrack(ubbe_request=self.request)

    def test_build_instructions(self):
        """
        Test TST Ship instructions
        """

        record = self.tst_track._get_carrier_account()

        self.assertIsInstance(record, CarrierAccount)

    def test_build(self):
        """
        Test TST Ship instructions
        """

        self.tst_track._build()

        self.assertIsInstance(self.tst_track._request, etree._Element)
        self.assertEqual(self.tst_track._request.tag, "tracingrequest")
