from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import RateSheet, RateSheetLane


class RateSheetLaneTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "user",
        "group",
        "markup",
        "carrier_markups",
        "account",
        "subaccount",
        "encryted_messages",
        "carrier_account",
        "ratesheet",
        "ratesheet_lane"
    ]
    ratesheet = mock.Mock(spec=RateSheet)
    ratesheet._state = Mock()
    lane_json = {
        "rate_sheet": ratesheet,
        "min_value": Decimal("3.3333"),
        "max_value": Decimal("2.2222"),
        "cost": Decimal("7.77")
    }

    def setUp(self):
        self.lane_json_full = {
            "rate_sheet": RateSheet.objects.get(pk=1),
            "min_value": Decimal("3.3333"),
            "max_value": Decimal("2.2222"),
            "cost": Decimal("7.77")
        }

    def test_create_empty(self):
        record = RateSheetLane.create()
        self.assertIsInstance(record, RateSheetLane)

    def test_create_full(self):
        record = RateSheetLane.create(self.lane_json)
        self.assertIsInstance(record, RateSheetLane)

    def test_set_values(self):
        record = RateSheetLane.create()
        record.set_values(self.lane_json)
        self.assertEqual(record.min_value, Decimal("3.3333"))

    def test_all_fields_verbose(self):
        record = RateSheetLane(**self.lane_json)
        self.assertIsInstance(record.rate_sheet, RateSheet)
        self.assertEqual(record.min_value, Decimal("3.3333"))
        self.assertEqual(record.max_value, Decimal("2.2222"))
        self.assertEqual(record.cost, Decimal("7.77"))

    def test_repr(self):
        expected = "< RateSheetLane (3.3333 2.2222 RateCost: $7.77 (1)) >"
        record = RateSheetLane(**self.lane_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "3.3333 2.2222 RateCost: $7.77 (1)"
        record = RateSheetLane(**self.lane_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        lane_json = {
            "rate_sheet": RateSheet.objects.get(pk=1),
            "min_value": Decimal("3.3323433"),
            "max_value": Decimal("2.2242322"),
            "cost": Decimal("7.77432477")
        }
        record = RateSheetLane(**lane_json)

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)
        self.assertIsInstance(record.rate_sheet, RateSheet)
        self.assertEqual(record.min_value, Decimal("3.3323"))
        self.assertEqual(record.max_value, Decimal("2.2242"))
        self.assertEqual(record.cost, Decimal("7.77"))
