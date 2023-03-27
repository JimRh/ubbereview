"""
    Title: Saved Broker Model Unit Tests
    Description: This file will contain all unit tests for saved brokers Model.
    Created: May 10, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import SavedBroker, SubAccount, Address, Contact


class SavedBrokerTests(TestCase):
    
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
        "subaccount"
    ]

    def setUp(self):
        self.sub_account = SubAccount.objects.first()
        self.address = Address.objects.first()
        self.contact = Contact.objects.first()

        self.saved_broker_json = {
            "sub_account": self.sub_account,
            "address": self.address,
            "contact": self.contact,
        }

    def test_create_empty(self):
        record = SavedBroker.create()
        self.assertIsInstance(record, SavedBroker)

    def test_create_full(self):
        record = SavedBroker.create(self.saved_broker_json)

        self.assertIsInstance(record, SavedBroker)
        self.assertEqual(record.sub_account, self.sub_account)
        self.assertEqual(record.address, self.address)
        self.assertEqual(record.contact, self.contact)

    def test_set_values(self):
        record = SavedBroker.create()
        record.set_values(self.saved_broker_json)
        record.sub_account = self.sub_account
        record.contact = self.contact
        self.assertIsInstance(record, SavedBroker)
        self.assertEqual(record.sub_account, self.sub_account)
        self.assertEqual(record.address, self.address)
        self.assertEqual(record.contact, self.contact)

    def test_all_fields_verbose(self):
        record = SavedBroker(**self.saved_broker_json)
        self.assertIsInstance(record, SavedBroker)
        self.assertEqual(record.sub_account, self.sub_account)
        self.assertEqual(record.address, self.address)
        self.assertEqual(record.contact, self.contact)

    def test_repr(self):
        expected = "< Saved Broker (< SubAccount (8cd0cae7-6a22-4477-97e1-a7ccfbed3e01) >: < Address (130 9 Avenue Se, Calgary, < Province (Alberta: AB, Canada: CA) >, T2G0P3) >, < Contact ( KenCar ) >) >"
        record = SavedBroker(**self.saved_broker_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "kenneth carmichael: 130 9 Avenue Se, Calgary, Alberta, Canada, T2G0P3, KenCar"
        record = SavedBroker(**self.saved_broker_json)
        self.assertEqual(expected, str(record))

    def test_save(self):

        record = SavedBroker.create(param_dict=self.saved_broker_json)
        record.sub_account = self.sub_account

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertIsInstance(record, SavedBroker)
        self.assertEqual(record.sub_account, self.sub_account)
        self.assertEqual(record.address, self.address)
        self.assertEqual(record.contact, self.contact)
