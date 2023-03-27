from datetime import datetime
from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from api.models import Shipment, Contact, Address, Carrier, SubAccount


# TODO: test: one_step_save, get_next_leg_info, create_leg, gen_id, shipment_id, _next_leg_packages, _next_leg_commodities, _next_leg_json, one_step_delete
class ShipmentTests(TestCase):
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
        "shipments"
    ]
    user = mock.Mock(spec=User)
    user._state = Mock()
    user._state.db = None
    contact = mock.Mock(spec=Contact)
    contact._state = Mock()
    contact._state.db = None
    address = mock.Mock(spec=Address)
    address._state = Mock()
    address._state.db = None
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    carrier._state.db = None

    shipment_json = {
        "shipment_id": "GO1234567890",
        "markup": Decimal('0'),
        "user": user,
        "sender": contact,
        "receiver": contact,
        "origin": address,
        "destination": address,
        "purchase_order": "TEST",
        "reference_one": "TEST",
        "reference_two": "TEST",
        "requested_pickup_time": datetime(year=1, month=1, day=1, tzinfo=timezone.utc).isoformat(),
        "requested_pickup_close_time": datetime(year=1, month=1, day=1, tzinfo=timezone.utc).isoformat(),
        "is_food": True
    }

    def setUp(self):
        self.shipment_json_full = {
            "shipment_id": "GO1234567890",
            "user": User.objects.get(pk=1),
            "sender": Contact.objects.get(pk=1),
            "receiver": Contact.objects.get(pk=1),
            "origin": Address.objects.get(pk=1),
            "destination": Address.objects.get(pk=1),
            "markup": Decimal('0'),
            "purchase_order": "TEST",
            "reference_one": "TEST",
            "reference_two": "TEST",
            "requested_pickup_time": datetime(year=1, month=1, day=1, tzinfo=timezone.utc).isoformat(),
            "requested_pickup_close_time": datetime(year=1, month=1, day=1, tzinfo=timezone.utc).isoformat(),
            "is_food": True
        }

    def test_create_empty(self):
        record = Shipment.create()
        self.assertIsInstance(record, Shipment)

    def test_create_full(self):
        record = Shipment.create(self.shipment_json)
        self.assertIsInstance(record, Shipment)

    def test_set_values(self):
        record = Shipment.create()
        record.set_values(self.shipment_json)
        self.assertEqual(record.purchase_order, "TEST")

    def test_all_fields_verbose(self):
        record = Shipment(**self.shipment_json)
        self.assertTrue(record.is_food)
        self.assertEqual(record.shipment_id, "GO1234567890")
        self.assertEqual(record.purchase_order, "TEST")
        self.assertEqual(record.reference_one, "TEST")
        self.assertEqual(record.reference_two, "TEST")
        self.assertEqual(record.requested_pickup_time,
                         datetime(year=1, month=1, day=1, tzinfo=timezone.utc).isoformat())
        self.assertEqual(record.requested_pickup_close_time,
                         datetime(year=1, month=1, day=1, tzinfo=timezone.utc).isoformat())
        self.assertIsInstance(record.user, User)
        self.assertIsInstance(record.sender, Contact)
        self.assertIsInstance(record.receiver, Contact)

    def test_repr(self):
        expected = "< Shipment (GO1234567890, kenneth: Edmonton to Edmonton) >"
        record = Shipment(**self.shipment_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "GO1234567890, Edmonton to Edmonton"
        record = Shipment(**self.shipment_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        shipment_json = {
            "subaccount": SubAccount.objects.first(),
            "user": User.objects.get(pk=1),
            "shipment_id": "GO0987654321",
            "markup": Decimal('0'),
            "cost": Decimal('0'),
            "freight": Decimal('0'),
            "surcharge": Decimal('0'),
            "tax": Decimal('0'),
            "origin": Address.objects.get(pk=1),
            "destination": Address.objects.get(pk=1),
            "sender": Contact.objects.get(pk=1),
            "receiver": Contact.objects.get(pk=1),
            "purchase_order": "0976-qwer",
            "reference_one": "6731",
            "reference_two": "4325",
        }
        shipment = Shipment(**shipment_json)

        shipment.save()
        self.assertIsInstance(Shipment.objects.get(shipment_id=shipment.shipment_id), Shipment)
        self.assertEqual(Shipment.objects.get(shipment_id=shipment.shipment_id).reference_two, "4325")
