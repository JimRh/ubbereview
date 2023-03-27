"""
    Title: Transaction Model Unit Tests
    Description: This file will contain all unit tests for transaction Model.
    Created: June 10, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils.timezone import utc

from api.models import Transaction, Shipment


class TransactionTests(TestCase):

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

    def setUp(self):
        self.shipment = Shipment.objects.first()
        self.date = datetime.strptime("2022-06-06 10:00", "%Y-%m-%d %H:%M")
        self.date = self.date.replace(tzinfo=utc)
        self.transaction_json = {
            "shipment": self.shipment,
            "transaction_date": self.date,
            "transaction_id": self.shipment.shipment_id,
            "transaction_number": "TEST_ID",
            "transaction_amount": Decimal("10.00"),
            "complete": "Complete",
            "card_type": "VISA",
            "is_pre_authorized": False,
            "is_captured": True,
            "is_payment": True
        }

    def test_create_empty(self):
        record = Transaction.create()
        self.assertIsInstance(record, Transaction)

    def test_create_full(self):
        record = Transaction.create(self.transaction_json)
        self.assertIsInstance(record, Transaction)

    def test_set_values(self):
        record = Transaction.create()
        record.set_values(self.transaction_json)
        record.shipment = self.shipment

        self.assertIsInstance(record, Transaction)
        self.assertEqual(record.shipment, self.shipment)
        self.assertEqual(record.transaction_date, self.date)
        self.assertEqual(record.transaction_id, self.shipment.shipment_id)
        self.assertEqual(record.transaction_number, "TEST_ID")
        self.assertEqual(record.transaction_amount, Decimal("10.00"))
        self.assertEqual(record.complete, "Complete")
        self.assertEqual(record.card_type, "VISA")
        self.assertFalse(record.is_pre_authorized)
        self.assertTrue(record.is_captured)
        self.assertTrue(record.is_payment)

    def test_all_fields_verbose(self):
        record = Transaction.create(self.transaction_json)

        self.assertIsInstance(record, Transaction)
        self.assertEqual(record.shipment, self.shipment)
        self.assertEqual(record.transaction_date, self.date)
        self.assertEqual(record.transaction_id, self.shipment.shipment_id)
        self.assertEqual(record.transaction_number, "TEST_ID")
        self.assertEqual(record.transaction_amount, Decimal("10.00"))
        self.assertEqual(record.complete, "Complete")
        self.assertEqual(record.card_type, "VISA")
        self.assertFalse(record.is_pre_authorized)
        self.assertTrue(record.is_captured)
        self.assertTrue(record.is_payment)

    def test_save(self):
        record = Transaction.create(self.transaction_json)
        record.save()

        self.assertIsInstance(record, Transaction)
        self.assertEqual(record.shipment, self.shipment)
        self.assertEqual(record.transaction_id, self.shipment.shipment_id)
        self.assertEqual(record.transaction_number, "TEST_ID")
        self.assertEqual(record.transaction_amount, Decimal("10.00"))
        self.assertEqual(record.complete, "Complete")
        self.assertEqual(record.card_type, "VISA")
        self.assertFalse(record.is_pre_authorized)
        self.assertTrue(record.is_captured)
        self.assertTrue(record.is_payment)

    def test_repr(self):
        record = Transaction.create(self.transaction_json)
        self.assertEqual(record.__repr__(), "< Transaction (GO8305884695, 2022-06-06 10:00:00+00:00: GO8305884695>")

    def test_str(self):
        record = Transaction.create(self.transaction_json)
        self.assertEqual(record.__str__(), "GO8305884695, 2022-06-06 10:00:00+00:00: GO8305884695")
