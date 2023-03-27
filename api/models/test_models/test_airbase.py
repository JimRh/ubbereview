from django.test import TestCase
from unittest import mock
from unittest.mock import Mock

from api.models import Airbase, Address, Carrier


# TODO: test: get_ship_dict
class AirbaseTests(TestCase):
    fixtures = [
        "countries",
        "provinces",
        "carriers",
        "addresses"
    ]
    address = mock.Mock(spec=Address)
    address._state = Mock()
    address._state.db = None
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    carrier._state.db = None
    airbase_json = {
        "address": address,
        "carrier": carrier,
        "code": "YEG"
    }

    def setUp(self):
        self.airbase_json_full = {
            "address": Address.objects.get(pk=1),
            "carrier": Carrier.objects.get(code=2),
            "code": "YEG"
        }

    def test_create_empty(self):
        record = Airbase.create()
        self.assertIsInstance(record, Airbase)

    def test_create_full(self):
        record = Airbase.create(self.airbase_json)
        self.assertIsInstance(record, Airbase)

    def test_set_values(self):
        record = Airbase.create()
        record.set_values(self.airbase_json)
        self.assertEqual(record.code, "YEG")

    def test_all_fields_verbose(self):
        record = Airbase.create(self.airbase_json)
        self.assertEqual(record.code, "YEG")
        self.assertIsInstance(record.address, Address)
        self.assertIsInstance(record.carrier, Carrier)

    def test_repr_no_address(self):
        expected = "< Airbase (YEG, FedEx: None, None) >"
        self.airbase_json_full["address"] = None
        record = Airbase.create(self.airbase_json_full)
        self.assertEqual(expected, repr(record))

    def test_repr(self):
        expected = "< Airbase (YEG, FedEx: Edmonton, CA) >"
        record = Airbase.create(self.airbase_json_full)
        self.assertEqual(expected, repr(record))

    def test_str_no_address(self):
        expected = "YEG, FedEx: None, None"
        self.airbase_json_full["address"] = None
        record = Airbase.create(self.airbase_json_full)
        self.assertEqual(expected, str(record))

    def test_str(self):
        expected = "YEG, FedEx: Edmonton, CA"
        record = Airbase.create(self.airbase_json_full)
        self.assertEqual(expected, str(record))

    # TODO: Improve
    def test_save(self):
        airbase_json = {
            "address": Address.objects.get(pk=1),
            "carrier": Carrier.objects.get(pk=1),
            "code": "YEG"
        }
        airbase = Airbase.create(airbase_json)

        airbase.save()
        self.assertIsInstance(airbase, Airbase)
        self.assertEqual(Airbase.objects.get(pk=1).code, "YEG")

    def test_get_ship_dict(self):
        pass
