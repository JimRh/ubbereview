from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import CarrierPickupRestriction, Carrier


class CarrierServiceTests(TestCase):

    fixtures = [
        "carriers"
    ]

    def setUp(self):
        self.carrier = Carrier.objects.get(code=601)
        self.carrier_pickup_json = {
            "carrier": self.carrier,
            "min_start_time": "08:00",
            "max_start_time": "10:00",
            "min_end_time": "14:00",
            "max_end_time": "16:00",
            "pickup_window": 2,
            "min_time_same_day": "14:00",
            "max_pickup_days": 20
        }

    def test_create_empty(self):
        record = CarrierPickupRestriction.create()
        record.carrier = self.carrier
        self.assertIsInstance(record, CarrierPickupRestriction)

    def test_create_full(self):
        record = CarrierPickupRestriction.create(self.carrier_pickup_json)
        record.carrier = self.carrier
        self.assertIsInstance(record, CarrierPickupRestriction)

    def test_set_values(self):
        record = CarrierPickupRestriction.create()
        record.set_values(self.carrier_pickup_json)
        record.carrier = self.carrier
        self.assertEqual(record.max_start_time, "10:00")

    def test_all_fields_verbose(self):
        record = CarrierPickupRestriction(**self.carrier_pickup_json)
        record.carrier = self.carrier
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.carrier, self.carrier)
        self.assertEqual(record.min_start_time, "08:00")
        self.assertEqual(record.max_start_time, "10:00")
        self.assertEqual(record.min_end_time, "14:00")
        self.assertEqual(record.max_end_time, "16:00")
        self.assertEqual(record.pickup_window, 2)
        self.assertEqual(record.min_time_same_day, "14:00")
        self.assertEqual(record.max_pickup_days, 20)

    def test_repr(self):
        expected = "< CarrierPickupRestriction (Action Express, 08:00, 16:00) >"
        record = CarrierPickupRestriction.create(self.carrier_pickup_json)
        record.carrier = self.carrier
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Action Express, 08:00, 16:00, 14:00"
        record = CarrierPickupRestriction.create(self.carrier_pickup_json)
        record.carrier = self.carrier
        self.assertEqual(expected, str(record))

    def test_save(self):

        record = CarrierPickupRestriction.create(self.carrier_pickup_json)
        record.carrier = self.carrier
        try:
            record.save()
        except ValidationError as e:
            self.fail(e)

        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.carrier, self.carrier)
        self.assertEqual(record.min_start_time, "08:00")
        self.assertEqual(record.max_start_time, "10:00")
        self.assertEqual(record.min_end_time, "14:00")
        self.assertEqual(record.max_end_time, "16:00")
        self.assertEqual(record.pickup_window, 2)
        self.assertEqual(record.min_time_same_day, "14:00")
        self.assertEqual(record.max_pickup_days, 20)
