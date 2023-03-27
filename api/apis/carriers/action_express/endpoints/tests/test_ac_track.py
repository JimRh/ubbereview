"""
    Title: Action Express Track Unit Tests
    Description: Unit Tests for the Action Express Track. Test Everything.
    Created: Sept 08, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

from django.test import TestCase

from api.apis.carriers.action_express.endpoints.ac_track import ActionExpressTrack
from api.exceptions.project import TrackException
from api.models import SubAccount, CarrierAccount


class ACTrackTests(TestCase):
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
        "taxes",
    ]

    def setUp(self):
        self.sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        self.sub_account_two = SubAccount.objects.last()

        self.response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 2,
            },
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T17:41:50",
                "Level": 3,
            },
        ]

        self.ac_track = ActionExpressTrack(ubbe_request={})

    def test_process_response_delivered(self) -> None:
        """
        Test tracking - delivered status.
        """

        ret = self.ac_track._process_response(response=self.response)
        del ret["delivered_datetime"]
        expected = {"status": "Delivered", "details": "Completed"}
        self.assertEqual(expected, ret)

    def test_process_response_empty(self) -> None:
        """
        Test tracking - nothing.
        """

        with self.assertRaises(TrackException) as context:
            ret = self.ac_track._process_response(response=[])

            self.assertEqual(
                "AE Track (L59): No Tracking status yet.", context.exception.message
            )

    def test_process_response_created(self) -> None:
        """
        Test tracking - created status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 1,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "Created", "details": "Submitted"}
        self.assertEqual(expected, ret)

    def test_process_response_pickup(self) -> None:
        """
        Test tracking - pickup status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 0,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "Pickup", "details": "Entered"}
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_one(self) -> None:
        """
        Test tracking - in transit status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 2,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "InTransit", "details": "In Transit"}
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_two(self) -> None:
        """
        Test tracking - in transit status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 6,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "InTransit", "details": "Assigned"}
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_three(self) -> None:
        """
        Test tracking - in transit status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 7,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "InTransit", "details": "Assigned (In Transit)"}
        self.assertEqual(expected, ret)

    def test_process_response_in_transit_four(self) -> None:
        """
        Test tracking - in transit status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 8,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "InTransit", "details": "Unassigned"}
        self.assertEqual(expected, ret)

    def test_process_response_canceled_one(self) -> None:
        """
        Test tracking - canceled status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 4,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "Canceled", "details": "Canceled"}
        self.assertEqual(expected, ret)

    def test_process_response_canceled_two(self) -> None:
        """
        Test tracking - canceled status.
        """
        response = [
            {
                "ID": "00000000-0000-0000-0000-000000000000",
                "Name": None,
                "Description": None,
                "Timestamp": "2021-08-30T15:43:11",
                "Level": 5,
            }
        ]

        ret = self.ac_track._process_response(response=response)
        expected = {"status": "Canceled", "details": "Canceled (Billable)"}
        self.assertEqual(expected, ret)

    def test_get_carrier_account(self) -> None:
        """
        Test tracking - get carrier account.
        """
        self.ac_track._get_carrier_account(sub_account=self.sub_account)
        self.assertIsInstance(self.ac_track._carrier_account, CarrierAccount)

    def test_get_carrier_account_two(self) -> None:
        """
        Test tracking - get carrier account.
        """
        self.ac_track._get_carrier_account(sub_account=self.sub_account_two)
        self.assertIsInstance(self.ac_track._carrier_account, CarrierAccount)
