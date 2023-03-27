
from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import TransitTime


class TransitTimeTests(TestCase):
    transit_json = {
        "origin": "YEG",
        "destination": "YEV",
        "rate_priority_id": 2,
        "rate_priority_code": "STND",
        "transit_min": 4,
        "transit_max": 7
    }

    def test_create_empty(self):
        record = TransitTime.create()
        self.assertIsInstance(record, TransitTime)

    def test_create_full(self):
        record = TransitTime.create(self.transit_json)
        self.assertIsInstance(record, TransitTime)

    def test_set_values(self):
        record = TransitTime.create()
        record.set_values(self.transit_json)
        self.assertEqual(record.origin, "YEG")
        self.assertEqual(record.destination, "YEV")
        self.assertEqual(record.rate_priority_id, 2)
        self.assertEqual(record.rate_priority_code, "STND")

    def test_all_fields_verbose(self):
        record = TransitTime.create(self.transit_json)
        self.assertEqual(record.origin, "YEG")
        self.assertEqual(record.destination, "YEV")
        self.assertEqual(record.rate_priority_id, 2)
        self.assertEqual(record.rate_priority_code, "STND")
        self.assertEqual(record.transit_min, 4)
        self.assertEqual(record.transit_max, 7)

    def test_repr(self):
        expected = "< TransitTime (YEG, YEV, 2, STND) >"
        record = TransitTime.create(self.transit_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "YEG to YEV, STND, 4-7"
        record = TransitTime.create(self.transit_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        transit_json = {
            "origin": "YEG",
            "destination": "YZF",
            "rate_priority_id": 2,
            "rate_priority_code": "STND",
            "transit_min": 4,
            "transit_max": 7
        }
        record = TransitTime.create(transit_json)
        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertEqual(record.origin, "YEG")
        self.assertEqual(record.destination, "YZF")
        self.assertEqual(record.rate_priority_id, 2)
        self.assertEqual(record.rate_priority_code, "STND")
        self.assertEqual(record.transit_min, 4)
        self.assertEqual(record.transit_max, 7)
