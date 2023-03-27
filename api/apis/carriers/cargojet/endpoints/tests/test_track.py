"""
    Title: Cargojet Track Unit Tests
    Description: Unit Tests for the Cargojet Track. Test Everything.
    Created: Sept 27, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

from django.test import TestCase

from api.apis.carriers.cargojet.endpoints.cj_track import CargojetTrack
from api.exceptions.project import TrackException
from api.models import SubAccount, CarrierAccount


class CJTrackTests(TestCase):
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
        "taxes",
    ]

    def setUp(self):
        self.sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        self.sub_account_two = SubAccount.objects.last()

        self.response = [
            {"Status": "BOOKED", "Station": "YEG", "Date": "24-SEP-2021 01:30:00:am"},
            {"Status": "ACCEPTED", "Station": "YEG", "Date": "24-SEP-2021 01:36:00:am"},
            {"Status": "DEPARTED", "Station": "YEG", "Date": "24-SEP-2021 03:29:00:am"},
            {"Status": "ARRIVED", "Station": "YWG", "Date": "24-SEP-2021 05:17:00:am"},
            {
                "Status": "CARGO ARRIVED",
                "Station": "YVR",
                "Date": "24-SEP-2021 10:15:00:am",
            },
            {
                "Status": "DELIVERED",
                "Station": "YVR",
                "Date": "24-SEP-2021 03:18:00:pm",
            },
        ]

        self.cj_track = CargojetTrack(ubbe_request={})

    def test_process_response_delivered(self) -> None:
        """
        Test tracking - delivered status.
        """

        ret = self.cj_track._process_response(response=self.response)
        del ret["delivered_datetime"]
        expected = {
            "status": "Delivered",
            "details": "Delivered in YVR on 24-SEP-2021 03:18:00:pm (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_one(self) -> None:
        """
        Test tracking - In Transit status.
        """
        response = [
            {
                "Status": "CARGO ARRIVED",
                "Station": "YVR",
                "Date": "24-SEP-2021 10:15:00:am",
            }
        ]

        ret = self.cj_track._process_response(response=response)
        expected = {
            "status": "InTransit",
            "details": "Cargo Arrived in YVR on 24-SEP-2021 10:15:00:am (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_two(self) -> None:
        """
        Test tracking - In Transit status.
        """
        response = [
            {"Status": "ARRIVED", "Station": "YWG", "Date": "24-SEP-2021 05:17:00:am"}
        ]

        ret = self.cj_track._process_response(response=response)
        expected = {
            "status": "InTransit",
            "details": "Arrived in YWG on 24-SEP-2021 05:17:00:am (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_three(self) -> None:
        """
        Test tracking - In Transit status.
        """
        response = [
            {"Status": "DEPARTED", "Station": "YEG", "Date": "24-SEP-2021 03:29:00:am"}
        ]

        ret = self.cj_track._process_response(response=response)
        expected = {
            "status": "InTransit",
            "details": "Departed YEG on 24-SEP-2021 03:29:00:am (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_process_response_pickup(self) -> None:
        """
        Test tracking - Pickup status.
        """
        response = [
            {"Status": "ACCEPTED", "Station": "YEG", "Date": "24-SEP-2021 01:36:00:am"}
        ]

        ret = self.cj_track._process_response(response=response)
        expected = {
            "status": "Pickup",
            "details": "Accepted in YEG on 24-SEP-2021 01:36:00:am (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_process_response_created(self) -> None:
        """
        Test tracking - Created status.
        """
        response = [
            {"Status": "BOOKED", "Station": "YEG", "Date": "24-SEP-2021 01:30:00:am"}
        ]

        ret = self.cj_track._process_response(response=response)
        expected = {
            "status": "Created",
            "details": "Booked in YEG on 24-SEP-2021 01:30:00:am (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_process_response_canceled(self) -> None:
        """
        Test tracking - Canceled status.
        """
        response = [
            {"Status": "CANCELED", "Station": "YEG", "Date": "24-SEP-2021 01:30:00:am"}
        ]

        ret = self.cj_track._process_response(response=response)
        expected = {
            "status": "Canceled",
            "details": "Canceled in YEG on 24-SEP-2021 01:30:00:am (UTC)",
        }
        self.assertEqual(expected, ret)

    def test_get_carrier_account(self) -> None:
        """
        Test tracking - get carrier account.
        """
        self.cj_track._get_carrier_account(sub_account=self.sub_account)
        self.assertIsInstance(self.cj_track._carrier_account, CarrierAccount)

    def test_get_carrier_account_two(self) -> None:
        """
        Test tracking - get carrier account.
        """
        self.cj_track._get_carrier_account(sub_account=self.sub_account_two)
        self.assertIsInstance(self.cj_track._carrier_account, CarrierAccount)

    def test_process_response_empty(self) -> None:
        """
        Test tracking - nothing.
        """

        with self.assertRaises(TrackException) as context:
            ret = self.cj_track._process_response(response=[])

            self.assertEqual(
                "CJ Track (L34): No Tracking status yet.", context.exception.message
            )
