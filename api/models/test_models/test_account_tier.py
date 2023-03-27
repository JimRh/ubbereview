from decimal import Decimal

from django.test import TestCase

from api.models import AccountTier


class AccountTierTests(TestCase):

    def setUp(self):
        self.tier_json = {
            "name": "Sample Tier",
            "base_cost": Decimal("5.00"),
            "user_cost": Decimal("1.00"),
            "shipment_cost": Decimal("2.00"),
            "carrier_cost":  Decimal("3.00"),
            "api_requests_per_minute_cost": Decimal("0.20"),
            "user_count": 5,
            "shipment_count": 200,
            "carrier_count": 0,
            "api_requests_per_minute_count": 60,
            "additional_user_count": 8,
            "additional_shipment_count": 0,
            "additional_carrier_count": 0,
            "additional_api_requests_count": 500
        }

    def test_create_empty(self):
        record = AccountTier.create()
        self.assertIsInstance(record, AccountTier)

    def test_create_full(self):
        record = AccountTier.create(self.tier_json)
        self.assertIsInstance(record, AccountTier)

    def test_all_fields_verbose(self):
        record = AccountTier.create(self.tier_json)
        self.assertEqual(record.name, "Sample Tier")
        self.assertEqual(record.base_cost, Decimal("5.00"))
        self.assertEqual(record.user_cost, Decimal("1.00"))
        self.assertEqual(record.shipment_cost, Decimal("2.00"))
        self.assertEqual(record.carrier_cost, Decimal("3.00"))
        self.assertEqual(record.api_requests_per_minute_cost, Decimal("0.20"))
        self.assertEqual(record.user_count, 5)
        self.assertEqual(record.shipment_count, 200)
        self.assertEqual(record.carrier_count, 0)
        self.assertEqual(record.api_requests_per_minute_count, 60)
        self.assertEqual(record.additional_user_count, 8)
        self.assertEqual(record.additional_shipment_count, 0)
        self.assertEqual(record.additional_carrier_count, 0)
        self.assertEqual(record.additional_api_requests_count, 500)

    def test_repr(self):
        expected = "< AccountTier(name=Sample Tier, base_cost=5.00) >"
        record = AccountTier.create(self.tier_json)
        self.assertEqual(repr(record), expected)

    def test_str(self):
        expected = "Sample Tier"
        record = AccountTier.create(self.tier_json)
        self.assertEqual(str(record), expected)
