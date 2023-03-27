from datetime import datetime
from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from api.models import OptionName, CarrierOption, Carrier


class CarrierOptionTests(TestCase):
    fixtures = [
        "option_name",
        "carriers"
    ]
    option = mock.Mock(spec=OptionName)
    option._state = Mock()
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    carrier._state.db = None
    datentime = datetime(1, 1, 1, tzinfo=timezone.utc)
    carrier_option_json = {
        "option": option,
        "carrier": carrier,
        "evaluation_expression": "TEST",
        "minimum_value": Decimal("7.77"),
        "maximum_value": Decimal("7.77"),
        "start_date": datentime,
        "end_date": datentime,
    }

    def setUp(self):
        self.carrier_option_json_full = {
            "option": OptionName.objects.get(pk=1),
            "carrier": Carrier.objects.get(code=2),
            "evaluation_expression": "TEST",
            "minimum_value": Decimal("7.77"),
            "maximum_value": Decimal("7.77"),
            "start_date": self.datentime,
            "end_date": self.datentime,
        }

    def test_create_empty(self):
        record = CarrierOption.create()
        self.assertIsInstance(record, CarrierOption)

    def test_create_full(self):
        record = CarrierOption.create(self.carrier_option_json)
        self.assertIsInstance(record, CarrierOption)

    def test_set_values(self):
        record = CarrierOption()
        record.set_values(self.carrier_option_json)
        self.assertEqual(record.evaluation_expression, "TEST")

    def test_all_fields_verbose(self):
        record = CarrierOption(**self.carrier_option_json)
        self.assertIsInstance(record.option, OptionName)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.evaluation_expression, "TEST")
        self.assertEqual(record.minimum_value, Decimal("7.77"))
        self.assertEqual(record.maximum_value, Decimal("7.77"))
        self.assertEqual(record.start_date, datetime(1, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(record.end_date, datetime(1, 1, 1, tzinfo=timezone.utc))

    def test_repr(self):
        expected = "< CarrierOption (Delivery Appointment: < Carrier (FedEx: 2) >) >"
        record = CarrierOption(**self.carrier_option_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Delivery Appointment: FedEx"
        record = CarrierOption(**self.carrier_option_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        carrier_option_json = {
            "option": OptionName.objects.get(pk=1),
            "carrier": Carrier.objects.get(code=2),
            "evaluation_expression": "TEST",
            "minimum_value": Decimal("7.7777"),
            "maximum_value": Decimal("7.7723"),
            "start_date": self.datentime,
            "end_date": self.datentime
        }
        record = CarrierOption(**carrier_option_json)

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)
        self.assertIsInstance(record.option, OptionName)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.evaluation_expression, "TEST")
        self.assertEqual(record.minimum_value, Decimal("7.78"))
        self.assertEqual(record.maximum_value, Decimal("7.77"))
        self.assertEqual(record.start_date, self.datentime)
        self.assertEqual(record.end_date, self.datentime)

    def test_clean(self):
        CarrierOption(**self.carrier_option_json_full).save()

        with self.assertRaises(ValidationError):
            CarrierOption.create(self.carrier_option_json_full).save()
