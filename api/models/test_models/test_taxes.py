from datetime import datetime
from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from api.models import Tax, Province


class TaxesTests(TestCase):
    fixtures = [
        "countries",
        "provinces"
    ]
    province = mock.Mock(spec=Province)
    province._state = Mock()
    datentime = datetime(1, 1, 1, tzinfo=timezone.utc)

    def setUp(self):
        self.taxes_json = {
            "province": Province.objects.get(pk=1),
            "tax_rate": Decimal("2.22"),
            "expiry": self.datentime
        }

        self.ab_province = Province.objects.get(code="AB", country__code="CA")
        self.taxes_json_full = {
            "province": self.ab_province,
            "tax_rate": Decimal("2.22"),
            "expiry": self.datentime
        }

    def test_create_empty(self):
        record = Tax.create()
        self.assertIsInstance(record, Tax)

    def test_create_full(self):
        record = Tax.create(self.taxes_json)
        self.assertIsInstance(record, Tax)

    def test_set_values(self):
        record = Tax.create()
        record.set_values(self.taxes_json)
        self.assertEqual(record.tax_rate, Decimal("2.22"))

    def test_all_fields_verbose(self):
        record = Tax(**self.taxes_json)
        self.assertIsInstance(record.province, Province)
        self.assertEqual(record.tax_rate, Decimal("2.22"))
        self.assertEqual(record.expiry, datetime(1, 1, 1, tzinfo=timezone.utc))

    def test_repr(self):
        expected = '< Taxes (< Province (Alberta: AB, Canada: CA) >: 2.22) >'
        record = Tax(**self.taxes_json_full)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Alberta, Canada: 2.22"
        record = Tax(**self.taxes_json_full)
        self.assertEqual(expected, str(record))

    def test_save(self):
        tax_json = {
            "province": self.ab_province,
            "tax_rate": Decimal("2.43222"),
            "expiry": self.datentime
        }
        record = Tax(**tax_json)

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)
        self.assertIsInstance(record.province, Province)
        self.assertEqual(record.tax_rate, Decimal("2.43"))
        self.assertEqual(record.expiry, self.datentime)
