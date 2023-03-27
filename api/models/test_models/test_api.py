from django.test import TestCase

from api.models import API


class APITests(TestCase):
    fixtures = [
        "api"
    ]
    api_json = {
        "name": "TEST",
        "active": False
    }

    def setUp(self):
        self.api_json_full = {
            "name": "TEST"
        }

    def test_create_empty(self):
        record = API.create()
        self.assertIsInstance(record, API)

    def test_create_full(self):
        record = API.create(self.api_json)
        self.assertIsInstance(record, API)

    def test_set_values(self):
        record = API.create()
        record.set_values(self.api_json)
        self.assertEqual(record.name, "TEST")

    def test_all_fields_verbose(self):
        record = API.create(self.api_json)
        self.assertEqual(record.name, "TEST")
        self.assertFalse(record.active)

    def test_repr_active(self):
        expected = "< API ( TEST : Active) >"
        record = API.create(self.api_json_full)
        self.assertEqual(expected, repr(record))

    def test_repr(self):
        expected = "< API ( TEST : Inactive) >"
        self.api_json_full["active"] = False
        record = API.create(self.api_json_full)
        self.assertEqual(expected, repr(record))

    def test_str_active(self):
        expected = "TEST: Active"
        record = API.create(self.api_json_full)
        self.assertEqual(expected, str(record))

    def test_str(self):
        expected = "TEST: Inactive"
        self.api_json_full["active"] = False
        record = API.create(self.api_json_full)
        self.assertEqual(expected, str(record))

    def test_create_save(self):
        record = API.create(self.api_json)
        record.save()
        self.assertIsInstance(record, API)
