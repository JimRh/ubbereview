"""
    Title: Purolator Service Unit Tests
    Description: Unit Tests for the Purolator Service. Test Everything.
    Created: Jan 7, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime

from django.test import TestCase
from django.utils import timezone

from api.apis.carriers.purolator.courier.endpoints.purolator_track import PurolatorTrack


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
        self.response = {
            "TrackingInformation": [
                {
                    "Scans": {
                        "Scan": [
                            {
                                "ScanType": "ProofOfPickUp",
                                "Depot": {"Name": "BURNABY, BC"},
                                "ScanDate": "2010-03-05",
                                "Description": "Picked up by Purolator",
                            }
                        ]
                    }
                }
            ]
        }

        self._puro_track = PurolatorTrack(ubbe_request={})

    def test_process_track_picked_up(self):
        expected = {
            "delivered_datetime": datetime.datetime(
                year=1, month=1, day=1, tzinfo=timezone.utc
            ),
            "estimated_delivery_datetime": datetime.datetime(
                year=1, month=1, day=1, tzinfo=timezone.utc
            ),
            "status": "Pickup",
            "details": "Picked up by Purolator BURNABY, BC",
        }

        ret = self._puro_track._process_track(response=self.response)
        self.assertDictEqual(expected, ret)

    def test_process_track_in_transit(self):
        copied = copy.deepcopy(self.response)
        copied["TrackingInformation"][0]["Scans"]["Scan"].insert(
            0,
            {
                "ScanType": "Other",
                "Depot": {"Name": "BURNABY, BC"},
                "ScanDate": "2010-03-05",
                "Description": "Shipment In Transit",
            },
        )

        expected = {
            "delivered_datetime": datetime.datetime(
                year=1, month=1, day=1, tzinfo=timezone.utc
            ),
            "estimated_delivery_datetime": datetime.datetime(
                year=1, month=1, day=1, tzinfo=timezone.utc
            ),
            "status": "InTransit",
            "details": "Shipment In Transit BURNABY, BC",
        }

        ret = self._puro_track._process_track(response=copied)
        self.assertDictEqual(expected, ret)

    def test_process_track_on_delivery(self):
        copied = copy.deepcopy(self.response)
        copied["TrackingInformation"][0]["Scans"]["Scan"].insert(
            0,
            {
                "ScanType": "OnDelivery",
                "Depot": {"Name": "MISSISSAUGA (WEST/OUEST), ON"},
                "ScanDate": "2010-03-08",
                "Description": "On vehicle for delivery",
                "ScanDetails": {"DeliveryAddress": "5995 AVEBURY MISSI"},
            },
        )

        expected = {
            "delivered_datetime": datetime.datetime(
                year=1, month=1, day=1, tzinfo=timezone.utc
            ),
            "estimated_delivery_datetime": datetime.datetime(
                year=1, month=1, day=1, tzinfo=timezone.utc
            ),
            "status": "OutForDelivery",
            "details": "On vehicle for delivery MISSISSAUGA (WEST/OUEST), ON to 5995 AVEBURY MISSI",
        }

        ret = self._puro_track._process_track(response=copied)
        self.assertDictEqual(expected, ret)

    def test_process_track_delivery(self):
        copied = copy.deepcopy(self.response)
        copied["TrackingInformation"][0]["Scans"]["Scan"].insert(
            0,
            {
                "ScanType": "Delivery",
                "Depot": {"Name": "MISSISSAUGA (WEST/OUEST), ON"},
                "ScanDate": "2010-03-08",
                "Description": "Delivered to",
                "ScanDetails": {
                    "DeliverySignature": "CARISSA",
                    "DeliveryAddress": "5995 AVEBURY MISSI",
                    "DeliveryCompanyName": "Head Office Mailroom",
                },
            },
        )

        expected = {
            "delivered_datetime": datetime.datetime(2010, 3, 8, 0, 0),
            "estimated_delivery_datetime": datetime.datetime(2010, 3, 8, 0, 0),
            "status": "Delivered",
            "details": "Delivered to MISSISSAUGA (WEST/OUEST), ON, to CARISSA at 5995 AVEBURY MISSI",
        }

        ret = self._puro_track._process_track(response=copied)
        self.assertDictEqual(expected, ret)
