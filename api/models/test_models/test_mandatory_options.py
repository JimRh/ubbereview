from datetime import datetime
from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from api.models import OptionName, MandatoryOption, Carrier


class MandatoryOptionTests(TestCase):
    fixtures = [
        "carriers",
        "option_name"
    ]
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    datentime = datetime(1, 1, 1, tzinfo=timezone.utc)
    mandatory_options_json = {
        "carrier": carrier,
        "evaluation_expression": "TEST",
        "minimum_value": Decimal("7.77"),
        "maximum_value": Decimal("7.77"),
        "start_date": datentime,
        "end_date": datentime,
    }

    def setUp(self):
        self.mandatory_options_json_full = {
            "carrier": Carrier.objects.get(code=2),
            "option": OptionName.objects.get(pk=7),
            "evaluation_expression": "TEST",
            "minimum_value": Decimal("7.77"),
            "maximum_value": Decimal("7.77"),
            "start_date": self.datentime,
            "end_date": self.datentime,
        }

    def test_create_empty(self):
        record = MandatoryOption.create()
        self.assertIsInstance(record, MandatoryOption)

    def test_create_full(self):
        record = MandatoryOption.create(self.mandatory_options_json)
        self.assertIsInstance(record, MandatoryOption)

    def test_set_values(self):
        record = MandatoryOption.create()
        record.set_values(self.mandatory_options_json)
        self.assertEqual(record.evaluation_expression, "TEST")

    def test_all_fields_verbose(self):
        record = MandatoryOption(**self.mandatory_options_json)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.evaluation_expression, "TEST")
        self.assertEqual(record.minimum_value, Decimal("7.77"))
        self.assertEqual(record.maximum_value, Decimal("7.77"))
        self.assertEqual(record.start_date, datetime(1, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(record.end_date, datetime(1, 1, 1, tzinfo=timezone.utc))

    def test_repr(self):
        expected = "< MandatoryOption (Residential Delivery: FedEx) >"
        record = MandatoryOption(**self.mandatory_options_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Residential Delivery: FedEx"
        record = MandatoryOption(**self.mandatory_options_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        mandatory_options_json = {
            "carrier": Carrier.objects.get(code=2),
            "option": OptionName.objects.get(pk=7),
            "evaluation_expression": "TEST",
            "minimum_value": Decimal("7.7777"),
            "maximum_value": Decimal("7.7722"),
            "start_date": self.datentime,
            "end_date": self.datentime
        }
        record = MandatoryOption(**mandatory_options_json)

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.evaluation_expression, "TEST")
        self.assertEqual(record.minimum_value, Decimal("7.78"))
        self.assertEqual(record.maximum_value, Decimal("7.77"))
        self.assertEqual(record.start_date, self.datentime)
        self.assertEqual(record.end_date, self.datentime)
