from decimal import Decimal

from django.test import TestCase

from api.globals.carriers import CAN_NORTH, PUROLATOR
from api.models import Markup, CarrierMarkup, Carrier


class CarrierMarkupTests(TestCase):
    fixtures = [
        "carriers",
        "markup",
        "carrier_markups"
    ]

    def test_create(self):
        params = {
            "markup": Markup.objects.first(),
            "carrier": Carrier.objects.first(),
            "percentage": Decimal("10.00")
        }

        record = CarrierMarkup.create(param_dict=params)

        self.assertIsInstance(record, CarrierMarkup)
        self.assertEqual(record.markup, Markup.objects.first())
        self.assertEqual(record.carrier, Carrier.objects.first())
        self.assertEqual(record.percentage, Decimal("10.00"))

    def test_repr(self):
        carrier_markup = CarrierMarkup.objects.get(pk=1)
        self.assertEqual(carrier_markup.__repr__(), "FedEx, Tier Two: 15.00%")

    def test_str(self):
        carrier_markup = CarrierMarkup.objects.get(pk=1)
        self.assertEqual(carrier_markup.__str__(), "FedEx, Tier Two: 15.00%")
