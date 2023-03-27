from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import CarrierService, Carrier


class CarrierServiceTests(TestCase):
    fixtures = [
        "carriers"
    ]
    carrier = mock.Mock(spec=Carrier)
    carrier._state = Mock()
    carrier_service_json = {
        "carrier": carrier,
        "name": "GENERAL",
        "code": "77",
        "description": "TODAY",
        "exceptions": "NONE",
        "service_days": "MONDAY TO FRIDAY",
        "is_international": True
    }

    def test_create_empty(self):
        record = CarrierService.create()
        self.assertIsInstance(record, CarrierService)

    def test_create_full(self):
        record = CarrierService.create(self.carrier_service_json)
        self.assertIsInstance(record, CarrierService)

    def test_set_values(self):
        record = CarrierService.create()
        record.set_values(self.carrier_service_json)
        self.assertEqual(record.name, "GENERAL")

    def test_all_fields_verbose(self):
        record = CarrierService(**self.carrier_service_json)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.name, "GENERAL")
        self.assertEqual(record.code, "77")
        self.assertEqual(record.description, "TODAY")
        self.assertEqual(record.exceptions, "NONE")
        self.assertEqual(record.service_days, "MONDAY TO FRIDAY")
        self.assertTrue(record.is_international)

    def test_repr(self):
        expected = "< CarrierService (GENERAL, TODAY) >"
        record = CarrierService.create(self.carrier_service_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "GENERAL, TODAY"
        record = CarrierService.create(self.carrier_service_json)
        self.assertEqual(expected, str(record))

