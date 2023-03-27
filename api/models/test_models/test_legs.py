from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Shipment, Leg, Address, Carrier


# TODO: test: one_step_save, create_or_find, find, get_all_undelivered_legs, leg_id, one_step_delete, next_leg_json, update_leg
class LegTests(TestCase):
    fixtures = [
        "countries",
        "provinces",
        "addresses",
        "carriers",
        "contact",
        "user",
        "group",
        "subaccount",
        "account",
        "markup",
        "shipments",
        "legs"
    ]
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    carrier._state.db = None
    address = mock.Mock(spec=Address)
    address._state = Mock()
    address._state.db = None

    leg_json = {
        "leg_id": "GO6789054321",
        "carrier": carrier,
        "origin": address,
        "destination": address,
        "tracking_identifier": "TEST",
        "carrier_pickup_identifier": "TEST",
        "service_code": "TEST",
        "service_name": "TEST",
        "transit_days": 7,
        "on_hold": False
    }

    def setUp(self):
        self.leg_json_full = {
            "leg_id": "GO6789054321M",
            "carrier": Carrier.objects.get(code=2),
            "origin": Address.objects.get(pk=1),
            "destination": Address.objects.get(pk=1),
            "tracking_identifier": "TEST",
            "carrier_pickup_identifier": "TEST",
            "service_code": "TEST",
            "service_name": "TEST",
            "transit_days": 7,
            "on_hold": False
        }

    def test_create_empty(self):
        record = Leg.create()
        self.assertIsInstance(record, Leg)

    def test_create_full(self):
        record = Leg.create(self.leg_json)
        self.assertIsInstance(record, Leg)

    def test_set_values(self):
        record = Leg.create()
        record.set_values(self.leg_json)
        self.assertEqual(record.service_code, "TEST")

    def test_all_fields_verbose(self):
        record = Leg(**self.leg_json)
        self.assertEqual(record.leg_id, "GO6789054321")
        self.assertEqual(record.tracking_identifier, "TEST")
        self.assertEqual(record.carrier_pickup_identifier, "TEST")
        self.assertEqual(record.service_code, "TEST")
        self.assertEqual(record.service_name, "TEST")
        self.assertEqual(record.transit_days, 7)
        self.assertFalse(record.on_hold)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertIsInstance(record.origin, Address)
        self.assertIsInstance(record.destination, Address)

    def test_repr_on_hold(self):
        expected = "< ShipmentLeg (GO6789054321M, FedEx: Edmonton to Edmonton, OnHold) >"
        self.leg_json_full["on_hold"] = True
        record = Leg(**self.leg_json_full)
        self.assertEqual(expected, repr(record))

    def test_repr_not_on_hold(self):
        expected = "< ShipmentLeg (GO6789054321M, FedEx: Edmonton to Edmonton, Shipped) >"
        record = Leg(**self.leg_json_full)
        self.assertEqual(expected, repr(record))

    def test_str_on_hold(self):
        expected = "GO6789054321M, FedEx: Edmonton to Edmonton, OnHold"
        self.leg_json_full["on_hold"] = True
        record = Leg(**self.leg_json_full)
        self.assertEqual(expected, str(record))

    def test_str_not_on_hold(self):
        expected = "GO6789054321M, FedEx: Edmonton to Edmonton, Shipped"
        record = Leg(**self.leg_json_full)
        self.assertEqual(expected, str(record))

