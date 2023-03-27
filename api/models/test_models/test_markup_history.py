import datetime

from django.test import TestCase

from api.models import Markup, MarkupHistory


class MarkupHistoryTests(TestCase):

    fixtures = [
        "markup",
    ]

    history_json = {
        "markup": Markup.objects.first(),
        "change_date": datetime.datetime.now(),
        "username": "Kenneth",
        "old_value": "10",
        "new_value": "15"
    }

    def test_create_empty(self):
        record = MarkupHistory.create()
        self.assertIsInstance(record, MarkupHistory)

    def test_create_full(self):
        record = MarkupHistory.create(self.history_json)
        self.assertIsInstance(record, MarkupHistory)

    def test_set_values(self):
        record = MarkupHistory.create()
        record.set_values(self.history_json)
        self.assertEqual(record.username, "Kenneth")
        self.assertEqual(record.old_value, "10")
        self.assertEqual(record.new_value, "15")

    def test_all_fields_verbose(self):
        record = MarkupHistory.create(self.history_json)
        record.markup = Markup.objects.first()
        self.assertEqual(record.markup, Markup.objects.first())
        self.assertEqual(record.username, "Kenneth")
        self.assertEqual(record.old_value, "10")
        self.assertEqual(record.new_value, "15")

    def test_repr(self):
        expected = "< MarkupHistory (Tier Three: 25.00%, Kenneth, 10, 15)"
        record = MarkupHistory.create(self.history_json)
        record.markup = Markup.objects.first()
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Tier Three: 25.00%: Kenneth, 10 to 15"
        record = MarkupHistory.create(self.history_json)
        record.markup = Markup.objects.first()
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = MarkupHistory.create(self.history_json)
        record.markup = Markup.objects.first()
        record.save()

        self.assertEqual(record.markup, Markup.objects.first())
        self.assertEqual(record.username, "Kenneth")
        self.assertEqual(record.old_value, "10")
        self.assertEqual(record.new_value, "15")
