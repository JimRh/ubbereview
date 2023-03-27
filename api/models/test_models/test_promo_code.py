from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase


from api.models.promo_code import PromoCode


class TestPromoCode(TestCase):

    promo_code_json = {
        "code": "test",
        "quantity": "3"
    }

    def test_create_empty(self):
        promocode = PromoCode.create()
        self.assertIsInstance(promocode, PromoCode)

    def test_promocode(self):
        promocode = PromoCode.create(self.promo_code_json)
        self.assertIsInstance(promocode, PromoCode)

    def test_set_value(self):
        promocode = PromoCode.create()
        promocode.quantity = 56
        self.assertEqual(promocode.quantity, 56)

    def test_get_value(self):
        promocode = PromoCode.create(self.promo_code_json)
        self.assertEqual(promocode.code, "test")

    def test_all_fields(self):
        promocode_json = {
            "code": "51OFF",
            "quantity": "320",
            "start_date": "2019-02-01",
            "end_date": "2019-06-04",
            "flat_amount": "22.34",
            "min_shipment_cost": "75.00",
            "max_discount": "202.34",
            "percentage": "33.40",
            "is_active": True,
            "is_bulk": True
        }
        promocode = PromoCode.create(promocode_json)
        self.assertEqual(promocode.code, "51OFF")
        self.assertEqual(promocode.quantity, "320")
        self.assertNotEqual(promocode.start_date, "2019-01-01")
        self.assertEqual(promocode.end_date, "2019-06-04")
        self.assertNotEqual(promocode.flat_amount, "33.32")
        self.assertEqual(promocode.min_shipment_cost, "75.00")
        self.assertEqual(promocode.max_discount, "202.34")
        self.assertEqual(promocode.percentage, "33.40")
        self.assertTrue(promocode.is_active)
        self.assertTrue(promocode.is_bulk)

    def test_promocode_save(self):
        promo_code = {
            "code": "TEST",
            "quantity": 43,
            "max_discount": Decimal("65.44"),

        }
        PromoCode.create(promo_code).save()
        self.assertTrue(PromoCode.objects.filter(code="TEST").exists())

