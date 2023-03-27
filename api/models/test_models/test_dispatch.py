
from django.test import TestCase

from api.models import Dispatch, Carrier, Contact


class DispatchTests(TestCase):

    fixtures = [
        "carriers",
        "contact",
        "test_dispatch"
    ]

    def setUp(self):
        self.carrier = Carrier.objects.get(code=601)
        self.contact = Contact.objects.first()

        self.dispatch_json = {
            "carrier": self.carrier,
            "contact": self.contact,
            "location": "TEST",
            "is_default": True
        }

    def test_create_empty(self):
        record = Dispatch.create()
        self.assertIsInstance(record, Dispatch)

    def test_create_full(self):
        record = Dispatch.create(self.dispatch_json)
        self.assertIsInstance(record, Dispatch)

    def test_set_values(self):
        record = Dispatch.create()
        record.set_values(self.dispatch_json)
        self.assertEqual(record.location, "TEST")
        self.assertTrue(record.is_default)

    def test_all_fields_verbose(self):
        record = Dispatch(**self.dispatch_json)
        self.assertEqual(record.location, "TEST")
        self.assertTrue(record.is_default)
        self.assertIsInstance(record.carrier, Carrier)

    def test_repr(self):
        expected = '< Dispatch (Action Express, TEST, Default: True) >'
        record = Dispatch.create(self.dispatch_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'Action Express, TEST, Default: True'
        record = Dispatch.create(self.dispatch_json)
        self.assertEqual(expected, str(record))

    def test_carrier_code(self):
        expected = 601
        record = Dispatch.objects.first()
        self.assertEqual(expected, record.carrier_code)

    def test_name(self):
        expected = 'KenCar'
        record = Dispatch.objects.first()
        self.assertEqual(expected, record.name)

    def test_phone(self):
        expected = '7809326245'
        record = Dispatch.objects.first()
        self.assertEqual(expected, record.phone)

    def test_email(self):
        expected = 'developer@bbex.com'
        record = Dispatch.objects.first()
        self.assertEqual(expected, record.email)
