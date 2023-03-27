
from django.test import TestCase

from api.models import ExchangeRate


class ExchangeRateTests(TestCase):

    def setUp(self):

        self.cad_to_usd_json = {
            "source_currency": "CAD",
            "target_currency": "USD",
            "exchange_rate": "5.109727"
        }

    def test_create_empty(self):
        record = ExchangeRate.create()
        self.assertIsInstance(record, ExchangeRate)

    def test_create_full(self):
        record = ExchangeRate.create(self.cad_to_usd_json)
        self.assertIsInstance(record, ExchangeRate)

    def test_set_values(self):
        record = ExchangeRate.create()
        record.set_values(self.cad_to_usd_json)
        self.assertEqual(record.source_currency, "CAD")
        self.assertEqual(record.target_currency, "USD")
        self.assertEqual(record.exchange_rate, "5.109727")

    def test_all_fields_verbose(self):
        record = ExchangeRate(**self.cad_to_usd_json)
        self.assertEqual(record.source_currency, "CAD")
        self.assertEqual(record.target_currency, "USD")
        self.assertEqual(record.exchange_rate, "5.109727")

    def test_repr(self):
        expected = '< ExchangeRate (CAD, USD, 5.109727)) >'
        record = ExchangeRate.create(self.cad_to_usd_json)
        record.save()
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'CAD, USD, 5.109727'
        record = ExchangeRate.create(self.cad_to_usd_json)
        record.save()
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = ExchangeRate.create(self.cad_to_usd_json)
        record.save()
        self.assertIsInstance(record, ExchangeRate)
