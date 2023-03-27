from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Leg, ShipDocument


class ShipDocumentTests(TestCase):
    fixtures = [
        "user",
        "group",
        "countries",
        "provinces",
        "carriers",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount",
        "shipments",
        "legs"
    ]
    leg = mock.Mock(spec=Leg)
    leg._state = Mock()
    leg._state.db = None
    ship_document_json = {
        "leg": leg,
        "type": 7,
        "document": "TEST"
    }

    def setUp(self):
        self.ship_document_json_full = {
            "leg": Leg.objects.get(pk=1),
            "type": 7,
            "document": "TEST"
        }

    def test_create_empty(self):
        record = ShipDocument.create()
        self.assertIsInstance(record, ShipDocument)

    def test_create_full(self):
        record = ShipDocument.create(self.ship_document_json)
        self.assertIsInstance(record, ShipDocument)

    def test_set_values(self):
        record = ShipDocument.create()
        record.set_values(self.ship_document_json)
        self.assertEqual(record.type, 7)

    def test_all_fields_verbose(self):
        record = ShipDocument(**self.ship_document_json)
        self.assertEqual(record.type, 7)
        self.assertEqual(record.document, "TEST")
        self.assertIsInstance(record.leg, Leg)

    def test_repr(self):
        expected = "< ShipDocument (GO7091160198D, 7) >"
        record = ShipDocument(**self.ship_document_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "GO7091160198D, 7"
        record = ShipDocument(**self.ship_document_json_full)
        self.assertEqual(expected, str(record))
