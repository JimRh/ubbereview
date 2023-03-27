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

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.twoship.endpoints.twoship_track_v2 import TwoShipTrack
from api.globals.carriers import UPS
from api.models import SubAccount, Carrier, CarrierAccount, Leg


class TwoShipTrackTests(TestCase):
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
        carrier = Carrier.objects.get(code=UPS)
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
                    UPS: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self._track_response = {
            "TrackingStatusCode": "DL",
            "TrackingStatusDescription": "Delivered - CA, , EDMONTON, T5M3W4",
            "EstimatedDeliveryDate": "0001-01-01T00:00:00",
            "DeliveryDate": "2023-01-11T12:34:00",
            "TrackingStatus": "Delivered",
            "SignatureBase64String": None,
            "SignedBy": None,
            "Events": [
                {
                    "ScanDate": "2023-01-10T19:52:00",
                    "Status": 1,
                    "Description": "Departed from Facility - CA, BC, Richmond, ",
                },
                {
                    "ScanDate": "2023-01-10T22:15:00",
                    "Status": 1,
                    "Description": "Arrived at Facility - CA, AB, Calgary, ",
                },
                {
                    "ScanDate": "2023-01-11T03:18:00",
                    "Status": 1,
                    "Description": "Departed from Facility - CA, AB, Calgary, ",
                },
                {
                    "ScanDate": "2023-01-11T06:45:00",
                    "Status": 1,
                    "Description": "Arrived at Facility - CA, AB, Edmonton, ",
                },
                {
                    "ScanDate": "2023-01-11T06:52:00",
                    "Status": 1,
                    "Description": "Out For Delivery - CA, AB, Edmonton, ",
                },
                {
                    "ScanDate": "2023-01-11T12:34:00",
                    "Status": 4,
                    "Description": "Delivered - CA, , EDMONTON, T5M3W4",
                },
            ],
            "OrderNo": None,
            "TrackingNumber": "",
            "ShipmentReference": None,
            "ShipmentPONumber": None,
        }

        self._two_track = TwoShipTrack(ubbe_request=self.request)

    def test_build_request(self):
        """
        Test TwoShip track request
        :return:
        """

        ret = self._two_track._build_request()
        expected = {"CarrierId": 708, "TrackingNumber": "518-YUX-10290383"}
        del ret["WS_Key"]
        self.assertDictEqual(expected, ret)

    def test_format_response_delivered(self):
        """
        Test TwoShip track for status delivered
        :return:
        """

        ret = self._two_track._format_response(response=self._track_response)
        expected = {
            "status": "Delivered",
            "details": "Delivered - CA, , EDMONTON, T5M3W4",
            "delivered_datetime": datetime.datetime(
                2023, 1, 11, 12, 34, tzinfo=datetime.timezone.utc
            ),
        }
        del ret["leg"]

        self.assertDictEqual(expected, ret)

    def test_format_response_undeliverablescan(self):
        """
        Test TwoShip  track for status undeliverablescan
        :return:
        """

        copied = copy.deepcopy(self._track_response)
        copied["TrackingStatus"] = "UndeliverableScan"

        ret = TwoShipTrack(ubbe_request=self.request)._format_response(response=copied)

        expected = {
            "status": "DeliveryException",
            "details": "Delivered - CA, , EDMONTON, T5M3W4",
        }
        del ret["leg"]

        self.assertDictEqual(expected, ret)

    def test_format_response_pick_up(self):
        """
        Test TwoShip  track for status pickup
        :return:
        """

        copied = copy.deepcopy(self._track_response)
        copied["TrackingStatus"] = "PickedUp"

        ret = TwoShipTrack(ubbe_request=self.request)._format_response(response=copied)

        expected = {"status": "Pickup", "details": "Delivered - CA, , EDMONTON, T5M3W4"}
        del ret["leg"]

        self.assertDictEqual(expected, ret)

    def test_format_response_created(self):
        """
        Test TwoShip track for status created
        :return:
        """

        copied = copy.deepcopy(self._track_response)
        copied["TrackingStatus"] = "Created"

        ret = TwoShipTrack(ubbe_request=self.request)._format_response(response=copied)

        expected = {
            "status": "Created",
            "details": "Delivered - CA, , EDMONTON, T5M3W4",
        }
        del ret["leg"]

        self.assertDictEqual(expected, ret)

    def test_format_response_out_for_delivery(self):
        """
        Test TwoShip track for status out for delivery
        :return:
        """

        copied = copy.deepcopy(self._track_response)
        copied["TrackingStatusDescription"] = "out for delivery right now."

        ret = TwoShipTrack(ubbe_request=self.request)._format_response(response=copied)

        expected = {
            "status": "OutForDelivery",
            "details": "out for delivery right now.",
        }
        del ret["leg"]

        self.assertDictEqual(expected, ret)
