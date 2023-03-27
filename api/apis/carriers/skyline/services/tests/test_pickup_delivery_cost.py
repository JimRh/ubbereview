from decimal import Decimal

from django.test import TestCase

from api.apis.carriers.skyline.services.pickup_delivery_cost import PickupDeliveryCost
from api.models import NorthernPDAddress


class PickupDeliveryCostTests(TestCase):
    fixtures = ["northern_pd"]

    def setUp(self):
        self.is_pickup = (False,)
        self.is_delivery = (False,)
        self.total_weight = (Decimal("15.00"),)
        self.total_dim = (Decimal("10.00"),)
        self.origin_city = ("Inuvik",)
        self.delivery_city = "Yellowknife"

        self.p_and_d = PickupDeliveryCost(
            is_pickup=True,
            is_delivery=True,
            total_weight=Decimal("15.00"),
            total_dim=Decimal("10.00"),
            origin_city="Inuvik",
            delivery_city="Yellowknife",
        )

        self.p_and_d_above = PickupDeliveryCost(
            is_pickup=True,
            is_delivery=True,
            total_weight=Decimal("10.00"),
            total_dim=Decimal("55.00"),
            origin_city="Inuvik",
            delivery_city="Yellowknife",
        )

        self.p_and_d_bad_city = PickupDeliveryCost(
            is_pickup=True,
            is_delivery=True,
            total_weight=Decimal("55.00"),
            total_dim=Decimal("10.00"),
            origin_city="Van",
            delivery_city="Van",
        )

    def test_create_surcharge(self):
        charge = self.p_and_d.create_surcharge(
            pickup_company_id=4,
            charge=Decimal("15.00"),
            definition_id=12,
            fee_name="Local Pickup Charge",
        )

        expected = {
            "Charge": Decimal("15.00"),
            "DefinitionId": 12,
            "FeeName": "Local Pickup Charge",
            "PickupCompanyId": 4,
        }

        self.assertIsInstance(charge, dict)
        self.assertDictEqual(charge, expected)

    def test_calculate_charge_below(self):
        charge = self.p_and_d.calculate_charge(
            airbase=NorthernPDAddress.objects.first()
        )

        self.assertIsInstance(charge, Decimal)
        self.assertEqual(charge, Decimal("18.00"))

    def test_calculate_charge_above(self):
        charge = self.p_and_d_above.calculate_charge(
            airbase=NorthernPDAddress.objects.first()
        )

        self.assertIsInstance(charge, Decimal)
        self.assertEqual(charge, Decimal("19.80"))

    def test_calculate_pickup(self):
        charge = self.p_and_d.calculate_pickup()

        expected = {
            "Charge": Decimal("18.00"),
            "DefinitionId": 104,
            "FeeName": "Local Pickup Charge",
            "PickupCompanyId": 13,
        }

        self.assertIsInstance(charge, dict)
        self.assertDictEqual(charge, expected)

    def test_calculate_pickup_fail(self):
        charge = self.p_and_d_bad_city.calculate_pickup()

        expected = {}

        self.assertIsInstance(charge, dict)
        self.assertDictEqual(charge, expected)

    def test_calculate_delivery(self):
        charge = self.p_and_d.calculate_delivery()

        expected = {
            "Charge": Decimal("18.00"),
            "DefinitionId": 105,
            "FeeName": "Local Delivery Charge",
            "PickupCompanyId": 60,
        }

        self.assertIsInstance(charge, dict)
        self.assertDictEqual(charge, expected)

    def test_calculate_delivery_fail(self):
        charge = self.p_and_d_bad_city.calculate_delivery()

        expected = {}

        self.assertIsInstance(charge, dict)
        self.assertDictEqual(charge, expected)

    def test_calculate_pickup_delivery(self):
        charge = self.p_and_d.calculate_pickup_delivery()

        expected = [
            {
                "Charge": Decimal("18.00"),
                "DefinitionId": 104,
                "FeeName": "Local Pickup Charge",
                "PickupCompanyId": 13,
            },
            {
                "Charge": Decimal("18.00"),
                "DefinitionId": 105,
                "FeeName": "Local Delivery Charge",
                "PickupCompanyId": 60,
            },
        ]

        self.assertIsInstance(charge, list)
        self.assertListEqual(charge, expected)
