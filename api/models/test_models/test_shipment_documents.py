from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Shipment, ShipmentDocument


class ShipmentDocumentTests(TestCase):
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
    shipment = mock.Mock(spec=Shipment)
    shipment._state = Mock()
    shipment._state.db = None
    shipment_document_json = {
        "shipment": shipment,
        "type": 7,
        "document": "TEST"
    }

    def setUp(self):
        self.shipment_document_json_full = {
            "shipment": Shipment.objects.get(pk=1),
            "type": 7,
            "document": "TEST"
        }

    def test_create_empty(self):
        record = ShipmentDocument.create()
        self.assertIsInstance(record, ShipmentDocument)

    def test_create_full(self):
        record = ShipmentDocument.create(self.shipment_document_json)
        self.assertIsInstance(record, ShipmentDocument)

    def test_set_values(self):
        record = ShipmentDocument.create()
        record.set_values(self.shipment_document_json)
        self.assertEqual(record.type, 7)

    def test_all_fields_verbose(self):
        record = ShipmentDocument(**self.shipment_document_json)
        self.assertEqual(record.type, 7)
        self.assertEqual(record.document, "TEST")
        self.assertIsInstance(record.shipment, Shipment)

    def test_repr(self):
        expected = "< ShipmentDocument (GO8305884695, 7) >"
        record = ShipmentDocument(**self.shipment_document_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "GO8305884695, 7"
        record = ShipmentDocument(**self.shipment_document_json_full)
        self.assertEqual(expected, str(record))
