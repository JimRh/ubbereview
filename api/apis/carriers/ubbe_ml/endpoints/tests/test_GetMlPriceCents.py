from django.core.exceptions import ObjectDoesNotExist

from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_base import MLCarrierBase
from django.test import TestCase
from api.models.ubbe_ml_regressors import UbbeMlRegressors


class GetMlPriceCentsTests(TestCase):
    """
    Test all logic, conversions, arithmetic of the get_ml_price_cents function
    The (lbs) weight bins are:
    {[0, 501),[501,1001),[1001,2001),[2001,5001),[5001,10001),[10001,+inf)}
    The units of the binned regressors is Canadian Dollars.
    """

    @staticmethod
    def lbs_to_kg(kg: float):
        """
        One pound is defined as 0.45359237 kg
        """
        return float(kg * 0.45359236999999)

    def setUp(self) -> None:
        """
        Setting up the coefficients to test.
        """
        regressors = UbbeMlRegressors(active=False)
        regressors.save()
        self.regressors = regressors
        weight_break_coefficients_m = [
            float(regressors.lbs_0_500_m),
            float(regressors.lbs_500_1000_m),
            float(regressors.lbs_1000_2000_m),
            float(regressors.lbs_2000_5000_m),
            float(regressors.lbs_5000_10000_m),
            float(regressors.lbs_10000_plus_m),
        ]
        weight_break_coefficients_b = [
            float(regressors.lbs_0_500_b),
            float(regressors.lbs_500_1000_b),
            float(regressors.lbs_1000_2000_b),
            float(regressors.lbs_2000_5000_b),
            float(regressors.lbs_5000_10000_b),
            float(regressors.lbs_10000_plus_b),
        ]
        min_price_coefficient_m = float(regressors.min_price_m)
        min_price_coefficient_b = float(regressors.min_price_b)
        self.weight_break_coefficients_m = weight_break_coefficients_m
        self.weight_break_coefficients_b = weight_break_coefficients_b
        self.min_price_coefficient_m = min_price_coefficient_m
        self.min_price_coefficient_b = min_price_coefficient_b

    def test(self):
        get_price = MLCarrierBase.get_ml_price_cents
        # Ensure it raises if there's no active model set
        with self.assertRaises(ObjectDoesNotExist):
            get_price(weight_kg=1.0, distance_km=100.0)
        self.regressors.active = True
        self.regressors.save()
        # First check a pre-calibrated price to see if it works
        i = get_price(weight_kg=1.0, distance_km=100.0)
        # Check that the function is returning an int, and that the minimum price is being returned for 1kg
        self.assertIsInstance(i, int)
        self.assertEqual(
            i,
            round(
                100.0
                * float(
                    float(self.min_price_coefficient_m * 100.0)
                    + self.min_price_coefficient_b
                )
            ),
        )
        # Test it returns -1 on weight <= 0, distance <= 0
        with self.assertRaises(ValueError):
            get_price(weight_kg=-0.1, distance_km=100.0)
        with self.assertRaises(ValueError):
            get_price(weight_kg=0, distance_km=100.0)
        with self.assertRaises(Exception):
            get_price(weight_kg=100.0, distance_km=0)
        # Check all weight breaks and the boundary conditions of all weight breaks
        break0 = get_price(weight_kg=self.lbs_to_kg(500), distance_km=100.0)
        self.assertEqual(
            round(break0),
            round(
                (
                    self.weight_break_coefficients_m[0] * 100.0
                    + self.weight_break_coefficients_b[0]
                )
                * 500
            ),
        )
        break1 = get_price(weight_kg=self.lbs_to_kg(501), distance_km=100.0)
        self.assertEqual(
            round(break1),
            round(
                (
                    self.weight_break_coefficients_m[1] * 100.0
                    + self.weight_break_coefficients_b[1]
                )
                * 501
            ),
        )

        break2 = get_price(weight_kg=self.lbs_to_kg(1000), distance_km=100.0)
        self.assertEqual(
            round(break2),
            round(
                (
                    self.weight_break_coefficients_m[1] * 100.0
                    + self.weight_break_coefficients_b[1]
                )
                * 1000
            ),
        )

        break3 = get_price(weight_kg=self.lbs_to_kg(1001), distance_km=100.0)
        self.assertEqual(
            round(break3),
            round(
                (
                    self.weight_break_coefficients_m[2] * 100.0
                    + self.weight_break_coefficients_b[2]
                )
                * 1001
            ),
        )

        break4 = get_price(weight_kg=self.lbs_to_kg(2000), distance_km=100.0)
        self.assertEqual(
            round(break4),
            round(
                (
                    self.weight_break_coefficients_m[2] * 100.0
                    + self.weight_break_coefficients_b[2]
                )
                * 2000
            ),
        )

        break5 = get_price(weight_kg=self.lbs_to_kg(2001), distance_km=100.0)
        self.assertEqual(
            round(break5),
            round(
                (
                    self.weight_break_coefficients_m[3] * 100.0
                    + self.weight_break_coefficients_b[3]
                )
                * 2001
            ),
        )

        break6 = get_price(weight_kg=self.lbs_to_kg(5000), distance_km=100.0)
        self.assertEqual(
            round(break6),
            round(
                (
                    self.weight_break_coefficients_m[3] * 100.0
                    + self.weight_break_coefficients_b[3]
                )
                * 5000
            ),
        )

        break7 = get_price(weight_kg=self.lbs_to_kg(5001), distance_km=100.0)
        self.assertEqual(
            round(break7),
            round(
                (
                    self.weight_break_coefficients_m[4] * 100.0
                    + self.weight_break_coefficients_b[4]
                )
                * 5001
            ),
        )

        break8 = get_price(weight_kg=self.lbs_to_kg(10000), distance_km=100.0)
        self.assertEqual(
            round(break8),
            round(
                (
                    self.weight_break_coefficients_m[4] * 100.0
                    + self.weight_break_coefficients_b[4]
                )
                * 10000
            ),
        )

        break9 = get_price(weight_kg=self.lbs_to_kg(10001), distance_km=100.0)
        self.assertEqual(
            round(break9),
            round(
                (
                    self.weight_break_coefficients_m[5] * 100.0
                    + self.weight_break_coefficients_b[5]
                )
                * 10001
            ),
        )

        break10 = get_price(weight_kg=self.lbs_to_kg(100001), distance_km=100.0)
        self.assertEqual(
            round(break10),
            round(
                (
                    self.weight_break_coefficients_m[5] * 100.0
                    + self.weight_break_coefficients_b[5]
                )
                * 100001
            ),
        )
