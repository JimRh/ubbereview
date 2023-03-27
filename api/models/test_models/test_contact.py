from django.test import TestCase

from api.models import Contact


class ContactTests(TestCase):
    contact_json = {
        "company_name": "Test",
        "name": "TEST",
        "phone": "7777777777",
        "email": "example@example.com",
    }

    def test_create_empty(self):
        record = Contact.create()
        self.assertIsInstance(record, Contact)

    def test_create_full(self):
        record = Contact.create(self.contact_json)
        self.assertIsInstance(record, Contact)

    def test_set_values(self):
        record = Contact.create()
        record.set_values(self.contact_json)
        self.assertEqual(record.name, "TEST")

    def test_all_fields_verbose(self):
        record = Contact.create(self.contact_json)
        self.assertEqual(record.company_name, "Test")
        self.assertEqual(record.name, "TEST")
        self.assertEqual(record.phone, "7777777777")
        self.assertEqual(record.email, "example@example.com")

    def test_repr(self):
        expected = "< Contact ( TEST ) >"
        record = Contact.create(self.contact_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST"
        record = Contact.create(self.contact_json)
        self.assertEqual(expected, str(record))

    def test_create_or_find(self):
        contact_json = {
            "name": "Bob",
            "phone": "1234567890",
            "email": "test@test.com",
            "company_name": "Test",
        }
        contact = Contact.create_or_find(contact_json)

        self.assertIsInstance(contact, Contact)
        self.assertEqual(contact.company_name, "Test")
