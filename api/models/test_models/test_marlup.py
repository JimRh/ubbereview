from decimal import Decimal

from django.test import TestCase

from api.globals.carriers import PUROLATOR, CAN_NORTH
from api.models import Markup, Carrier, CarrierMarkup


class MarkupTests(TestCase):
    fixtures = [
        "carriers",
        "markup",
        "carrier_markups"
    ]

    markup = {
        "name": "Tier One",
        "description": "Tier One Clients",
        "default_percentage": Decimal("15.00")
    }

    def test_save(self):
        record = Markup.create(self.markup)
        record.save()
        self.assertIsInstance(record, Markup)
        self.assertEqual(record.name, "Tier One")

    def test_markup_multiplier_exception(self):
        markup = Markup.objects.get(pk=2)
        markup_multiplier = markup.markup_multiplier(carrier_id=2)

        self.assertEqual(markup_multiplier, Decimal('1.25'))

    def test_markup_multiplier(self):
        markup = Markup.objects.get(pk=1)
        markup_multiplier = markup.markup_multiplier(carrier_id=2)

        self.assertEqual(markup_multiplier, Decimal('1.30'))

    def test_get_carrier_percentage_exception(self):
        markup = Markup.objects.get(pk=2)
        percentage = markup.get_carrier_percentage(carrier=Carrier.objects.first())

        self.assertEqual(percentage, Decimal('25'))

    def test_get_carrier_percentage(self):
        markup = Markup.objects.get(pk=1)
        percentage = markup.get_carrier_percentage(carrier=Carrier.objects.get(code=2))

        self.assertEqual(percentage, Decimal('15'))

    def test_repr(self):
        markup = Markup.objects.get(pk=1)
        self.assertEqual(markup.__repr__(), "Tier Two: 15.00%")

    def test_str(self):
        markup = Markup.objects.get(pk=1)
        self.assertEqual(markup.__str__(), "Tier Two: 15.00%")
