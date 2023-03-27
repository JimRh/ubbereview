"""
    Title: RateSheet Model Unit Tests
    Description: This file will contains all Unit Tests for RateSheet Model.
    Created: October 27, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.test import TestCase

from api.models import RateSheet, Carrier, Province


class RateSheetTests(TestCase):

    fixtures = [
        "carriers",
        "countries",
        "provinces"
    ]

    def setUp(self):
        self.rate_sheet_json = {
            "origin_province": Province.objects.get(pk=1),
            "destination_province": Province.objects.get(pk=2),
            "carrier": Carrier.objects.first(),
            "origin_city": "TEST",
            "destination_city": "TEST",
            "minimum_charge": Decimal("7.77"),
            "transit_days": 1,
            "service_code": "TEST",
            "service_name": "TEST",
            "availability": "TEST"
        }

        self.rate_sheet_json_full = {
            "origin_province": Province.objects.get(code="AB", country__code="CA"),
            "destination_province": Province.objects.get(code="AB", country__code="CA"),
            "carrier": Carrier.objects.get(code=2),
            "origin_city": "TEST",
            "destination_city": "TEST",
            "minimum_charge": Decimal("7.77"),
            "transit_days": 1,
            "service_code": "TEST",
            "service_name": "TEST",
            "availability": "TEST"
        }

    def test_create_empty(self):
        record = RateSheet.create()
        self.assertIsInstance(record, RateSheet)

    def test_create_full(self):
        record = RateSheet.create(self.rate_sheet_json)
        self.assertIsInstance(record, RateSheet)

    def test_set_values(self):
        record = RateSheet.create()
        record.set_values(self.rate_sheet_json)
        self.assertEqual(record.minimum_charge, Decimal("7.77"))

    def test_all_fields_verbose(self):
        record = RateSheet(**self.rate_sheet_json)
        self.assertIsInstance(record.origin_province, Province)
        self.assertIsInstance(record.destination_province, Province)
        self.assertIsInstance(record.carrier, Carrier)
        self.assertEqual(record.origin_city, "TEST")
        self.assertEqual(record.destination_city, "TEST")
        self.assertEqual(record.minimum_charge, Decimal("7.77"))
        self.assertEqual(record.maximum_charge, Decimal("0.00"))
        self.assertEqual(record.cut_off_time, "13:30")
        self.assertEqual(record.transit_days, 1)
        self.assertEqual(record.service_code, "TEST")
        self.assertEqual(record.service_name, "TEST")
        self.assertEqual(record.availability, "TEST")
        self.assertEqual(record.expiry_date.isoformat(), "0001-01-01T00:00:00+00:00")

    def test_repr(self):
        expected = "< RateSheet (2: TEST, AB, CA to TEST, AB, CA (None)) >"
        record = RateSheet(**self.rate_sheet_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "FedEx: TEST, AB, CA to TEST, AB, CA"
        record = RateSheet(**self.rate_sheet_json_full)
        self.assertEqual(expected, str(record))

    def test_clean_city(self):
        pass

    def test_save(self):
        pass
