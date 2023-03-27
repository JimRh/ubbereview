
from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import CNInterline


class CNInterlineTests(TestCase):
    interline_json = {
        "origin": "YEG",
        "destination": "YWJ",
        "interline_id": 7472,
        "interline_carrier": "Northwright Airlines"
    }

    def test_create_empty(self):
        record = CNInterline.create()
        self.assertIsInstance(record, CNInterline)

    def test_create_full(self):
        record = CNInterline.create(self.interline_json)
        self.assertIsInstance(record, CNInterline)

    def test_set_values(self):
        record = CNInterline.create()
        record.set_values(self.interline_json)
        self.assertEqual(record.origin, "YEG")
        self.assertEqual(record.destination, "YWJ")
        self.assertEqual(record.interline_id, 7472)
        self.assertEqual(record.interline_carrier, "Northwright Airlines")

    def test_all_fields_verbose(self):
        record = CNInterline.create(self.interline_json)
        self.assertEqual(record.origin, "YEG")
        self.assertEqual(record.destination, "YWJ")
        self.assertEqual(record.interline_id, 7472)
        self.assertEqual(record.interline_carrier, "Northwright Airlines")

    def test_repr(self):
        expected = "< CNInterline (YEG, YWJ, 7472, Northwright Airlines) >"
        record = CNInterline.create(self.interline_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "YEG to YWJ, 7472, Northwright Airlines"
        record = CNInterline.create(self.interline_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        interline_json = {
            "origin": "YZF",
            "destination": "YWJ",
            "interline_id": 7474,
            "interline_carrier": "Northwright Airlines"
        }
        record = CNInterline.create(interline_json)
        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertEqual(record.origin, "YZF")
        self.assertEqual(record.destination, "YWJ")
        self.assertEqual(record.interline_id, 7474)
        self.assertEqual(record.interline_carrier, "Northwright Airlines")
