import datetime
from decimal import Decimal

from django.test.testcases import TestCase
from django.utils import timezone

from api.models import Port, SealiftSailingDates, Carrier


class PortTests(TestCase):

    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "ports",
        "sailing_dates"
    ]

    def setUp(self):
        self.carrier = Carrier.objects.first()
        self.port = Port.objects.first()

        self.sailing_date = datetime.datetime.strptime("2019-06-16", "%Y-%m-%d").replace(tzinfo=timezone.utc)
        self.dg_packing_cutoff = datetime.datetime.strptime("2019-05-31", "%Y-%m-%d").replace(tzinfo=timezone.utc)
        self.cargo_packing_cutoff = datetime.datetime.strptime("2019-06-05", "%Y-%m-%d").replace(tzinfo=timezone.utc)
        self.bbe_dg_cutoff = datetime.datetime.strptime("2019-05-24", "%Y-%m-%d").replace(tzinfo=timezone.utc)
        self.bbe_cargo_cutoff = datetime.datetime.strptime("2019-05-29", "%Y-%m-%d").replace(tzinfo=timezone.utc)

        self.sailing_json = {
            "carrier": self.carrier,
            "port": self.port,
            "name": "FI",
            "sailing_date": self.sailing_date,
            "dg_packing_cutoff": self.dg_packing_cutoff,
            "cargo_packing_cutoff": self.cargo_packing_cutoff,
            "bbe_dg_cutoff": self.bbe_dg_cutoff,
            "bbe_cargo_cutoff": self.bbe_cargo_cutoff,
            "weight_capacity": "10000.00",
            "current_weight": "0.00",
            "status": "EP",
        }

    def test_create_empty(self):
        record = SealiftSailingDates.create()
        self.assertIsInstance(record, SealiftSailingDates)

    def test_create_full(self):
        record = SealiftSailingDates.create(self.sailing_json)
        self.assertIsInstance(record, SealiftSailingDates)

    def test_set_values(self):
        record = SealiftSailingDates.create()
        record.set_values(self.sailing_json)
        self.assertEqual(record.name, "FI")

    def test_all_fields_verbose(self):
        record = SealiftSailingDates(**self.sailing_json)

        self.assertEqual(record.name, "FI")
        self.assertEqual(record.carrier, self.carrier)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.port, self.port)
        self.assertIsInstance(record.port, Port)
        self.assertEqual(record.sailing_date, self.sailing_date)
        self.assertEqual(record.dg_packing_cutoff, self.dg_packing_cutoff)
        self.assertEqual(record.cargo_packing_cutoff, self.cargo_packing_cutoff)
        self.assertEqual(record.bbe_dg_cutoff, self.bbe_dg_cutoff)
        self.assertEqual(record.bbe_cargo_cutoff, self.bbe_cargo_cutoff)
        self.assertEqual(record.weight_capacity, "10000.00")
        self.assertEqual(record.current_weight, "0.00")
        self.assertEqual(record.status, "EP")

    def test_all_fields_save(self):
        record = SealiftSailingDates(**self.sailing_json)
        record.save()
        self.assertEqual(record.name, "FI")
        self.assertEqual(record.carrier, self.carrier)
        self.assertIsInstance(record.carrier, Carrier)

    def test_repr(self):
        expected = "< SealiftSailingDates (NEAS - FI - 2019-06-16) >"
        sailing = SealiftSailingDates.objects.first()
        self.assertEqual(expected, repr(sailing))

    def test_str(self):
        expected = "NEAS - FI - 2019-06-16"
        sailing = SealiftSailingDates.objects.first()
        self.assertEqual(expected, str(sailing))
