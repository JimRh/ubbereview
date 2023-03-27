import datetime
from decimal import Decimal
from unittest.mock import patch

import pytz
from django.test import TestCase
from django.utils import timezone

from api import models
from api.apis.services.taxes.taxes import Taxes


class TaxesTest(TestCase):
    fixtures = [
        "api",
        "countries",
        "provinces"
    ]

    def setUp(self):
        self.params = {
            "country": "CA",
            "postal_code": "XXXXXX",
            "province": "AB",
            "city": "Edmonton"
        }

    def test_taxes_check_date_good(self):
        self.assertTrue(
            Taxes._is_tax_rate_expired(
                (datetime.datetime.now() - datetime.timedelta(days=7)).replace(tzinfo=pytz.UTC)
            )
        )

    def test_taxes_check_date_bad(self):
        self.assertFalse(
            Taxes._is_tax_rate_expired(
                (datetime.datetime.now() + datetime.timedelta(days=7)).replace(tzinfo=pytz.UTC)
            )
        )

    @staticmethod
    def return_decimal(var):
        return Decimal("10.00")

    @patch("api.apis.services.taxes.taxes.Taxes._fetch_tax_rate", new=return_decimal)
    def test_taxes_get_taxes_no_item_in_database(self):
        self.assertEqual(Decimal("10.00"), Taxes(self.params).get_tax_rate(Decimal("100.00")))
        self.assertEqual(1, models.Tax.objects.all().count())

    @patch("api.apis.services.taxes.taxes.Taxes._fetch_tax_rate", new=return_decimal)
    def test_taxes_get_taxes_rate_in_database(self):
        new_tax = models.Tax()
        new_tax.province = models.Province.objects.get(pk=1)
        new_tax.tax_rate = Decimal("20.00")
        new_tax.expiry = timezone.now() + datetime.timedelta(days=5)
        new_tax.save()

        tax = Taxes(self.params).get_tax_rate(Decimal("100.00"))
        self.assertEqual(Decimal("20.00"), tax)
        self.assertEqual(1, models.Tax.objects.all().count())
        self.assertEqual(Decimal("20.00"), models.Tax.objects.get(pk=1).tax_rate)

    @patch("api.apis.services.taxes.taxes.Taxes._fetch_tax_rate", new=return_decimal)
    def test_taxes_get_taxes_rate_in_database_old(self):
        new_tax = models.Tax()
        new_tax.province = models.Province.objects.get(pk=1)
        new_tax.tax_rate = Decimal("20.00")
        new_tax.expiry = timezone.now() - datetime.timedelta(days=20)
        new_tax.save()

        tax = Taxes(self.params).get_tax_rate(Decimal("100.00"))
        self.assertEqual(Decimal("10.00"), tax)
        self.assertEqual(Decimal("10.00"), models.Tax.objects.get(pk=1).tax_rate)
