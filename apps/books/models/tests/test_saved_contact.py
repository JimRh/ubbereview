"""
    Title: Saved Contact Tests
    Description:  Saved Contact Tests of all methods.
    Created: February 09, 2023
    Author: Yusuf
    Edited By:
    Edited Date:
"""

from django.test import TestCase
from api.models import SubAccount, Contact
from apps.books.models import SavedContact


class SavedContactTest(TestCase):

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
    ]

    def setUp(self):
        """
        Saved Contact model test setup
        """
        self.account = SubAccount.objects.first()
        self.contact = Contact.objects.first()
        self.contact_last = Contact.objects.last()

        self.save_contact_full_json = {
            "sub_account": self.account,
            "username": "test123",
            "contact_hash": "adsjnnkl",
            "contact": self.contact,
            "is_origin": True,
            "is_destination": True,
            "is_vendor": True
        }

        self.save_contact_json = {
            "sub_account": self.account,
            "contact_hash": "adsjnnkl",
            "username": "test1234",
            "contact": self.contact_last
        }

    def test_create_empty(self):
        """
        Tests creating an empty saved contact
        """
        record = SavedContact.create()
        self.assertIsInstance(record, SavedContact)

    def test_create_full(self):
        """
        Tests creating a saved contact using all required details
        """
        record = SavedContact.create(param_dict=self.save_contact_full_json)
        self.assertIsInstance(record, SavedContact)

    def test_create(self):
        """
        Tests creating a saved contact using some required details

        """
        record = SavedContact.create(param_dict=self.save_contact_json)
        self.assertIsInstance(record, SavedContact)

    def test_set_values(self):
        """
        Tests Saved Contact set value method

        """
        record = SavedContact.create()
        record.set_values(pairs=self.save_contact_full_json)
        record.contact = self.save_contact_full_json["contact"]

        self.assertEqual(record.username, "test123")
        self.assertEqual(record.contact, self.contact)
        self.assertEqual(record.is_origin, True)
        self.assertEqual(record.is_destination, True)
        self.assertEqual(record.is_vendor, True)

    def test_all_fields_verbose(self):
        """
        Tests all fields in a created saved contact
        """
        record = SavedContact.create(self.save_contact_json)

        self.assertEqual(record.username, "test1234")
        self.assertEqual(record.contact, self.contact_last)
        self.assertEqual(record.is_origin, False)
        self.assertEqual(record.is_destination, False)
        self.assertEqual(record.is_vendor, False)

    def test_str(self):
        """
        Tests Saved Contact str method
        """
        record = SavedContact.create(self.save_contact_json)
        record.account = self.account
        record.save()

        expected = "kenneth carmichael: Testing Inc Two, Origin: False, Destination: False"
        self.assertEqual(str(record), expected)

    def test_repr(self):
        """
        Tests Saved Contact repr method
        """
        record = SavedContact.create(self.save_contact_full_json)
        record.account = self.account
        record.save()
        expected = "< Saved Contact (kenneth carmichael, KenCar, Origin True, Destination True"
        self.assertEqual(repr(record), expected)
