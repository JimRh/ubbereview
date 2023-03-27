from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Shipment, Leg, TrackingStatus


class TrackingStatusTests(TestCase):
    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "user",
        "group",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount",
        "shipments",
        "legs",
        "tracking_statuses"
    ]
    leg = mock.Mock(spec=Leg)
    leg._state = Mock()
    leg._state.db = None
    tracking_status_json = {
        "leg": leg,
        "delivered_datetime": "2018-05-08T14:00:00.000000-00:00",
        "estimated_delivery_datetime": "2018-05-08T13:00:00.000000-00:00",
        "status": "TEST",
        "details": "TEST"
    }

    def setUp(self):
        self.leg = Leg.objects.get(pk=1)
        self.shipment = Shipment.objects.get(pk=1)
        self.tracking_status_json_full = {
            "leg": self.leg,
            "delivered_datetime": "2018-05-08T14:00:00.000000-00:00",
            "estimated_delivery_datetime": "2018-05-08T13:00:00.000000-00:00",
            "status": "TEST",
            "details": "TEST"
        }

    def test_create_empty(self):
        record = TrackingStatus.create()
        self.assertIsInstance(record, TrackingStatus)

    def test_create_full(self):
        record = TrackingStatus.create(self.tracking_status_json)
        self.assertIsInstance(record, TrackingStatus)

    def test_set_values(self):
        record = TrackingStatus.create()
        record.set_values(self.tracking_status_json)
        self.assertEqual(record.status, "TEST")

    def test_all_fields_verbose(self):
        record = TrackingStatus(**self.tracking_status_json)
        self.assertEqual(record.delivered_datetime, "2018-05-08T14:00:00.000000-00:00")
        self.assertEqual(record.estimated_delivery_datetime, "2018-05-08T13:00:00.000000-00:00")
        self.assertEqual(record.status, "TEST")
        self.assertEqual(record.details, "TEST")
        self.assertIsInstance(record.leg, Leg)

    def test_repr(self):
        expected = "< TrackingStatus (GO7091160198D: TEST) >"
        record = TrackingStatus(**self.tracking_status_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "GO7091160198D: TEST"
        record = TrackingStatus(**self.tracking_status_json_full)
        self.assertEqual(expected, str(record))
