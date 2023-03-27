import datetime

from django.test import TestCase

from api.models import CarrierMarkup, CarrierMarkupHistory


class CarrierMarkupHistoryTests(TestCase):

    fixtures = [
        "markup",
        "carriers",
        "carrier_markups"
    ]

    history_json = {
        "carrier_markup": CarrierMarkup.objects.first(),
        "change_date": datetime.datetime.now(),
        "username": "Kenneth",
        "old_value": "10",
        "new_value": "15"
    }

    def test_create_empty(self):
        record = CarrierMarkupHistory.create()
        self.assertIsInstance(record, CarrierMarkupHistory)

    def test_create_full(self):
        record = CarrierMarkupHistory.create(self.history_json)
        self.assertIsInstance(record, CarrierMarkupHistory)

    def test_set_values(self):
        record = CarrierMarkupHistory.create()
        record.set_values(self.history_json)
        self.assertEqual(record.username, "Kenneth")
        self.assertEqual(record.old_value, "10")
        self.assertEqual(record.new_value, "15")

    def test_all_fields_verbose(self):
        record = CarrierMarkupHistory.create(self.history_json)
        record.carrier_markup = CarrierMarkup.objects.first()
        self.assertEqual(record.carrier_markup, CarrierMarkup.objects.first())
        self.assertEqual(record.username, "Kenneth")
        self.assertEqual(record.old_value, "10")
        self.assertEqual(record.new_value, "15")

    def test_repr(self):
        expected = "< CarrierMarkupHistory (Canadian North, Tier Two: 15.00%, Kenneth, 10, 15)"
        record = CarrierMarkupHistory.create(self.history_json)
        record.carrier_markup = CarrierMarkup.objects.first()
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Canadian North, Tier Two: 15.00%, Kenneth, 10 to 15"
        record = CarrierMarkupHistory.create(self.history_json)
        record.carrier_markup = CarrierMarkup.objects.first()
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = CarrierMarkupHistory.create(self.history_json)
        record.carrier_markup = CarrierMarkup.objects.first()
        record.save()

        self.assertEqual(record.carrier_markup, CarrierMarkup.objects.first())
        self.assertEqual(record.username, "Kenneth")
        self.assertEqual(record.old_value, "10")
        self.assertEqual(record.new_value, "15")

    def test_carrier(self):
        record = CarrierMarkupHistory.create(self.history_json)
        record.carrier_markup = CarrierMarkup.objects.first()
        record.save()
        self.assertEqual(record.carrier, "Canadian North")

    def test_markup(self):
        record = CarrierMarkupHistory.create(self.history_json)
        record.carrier_markup = CarrierMarkup.objects.first()
        record.save()
        self.assertEqual(record.markup, "Tier Two")
