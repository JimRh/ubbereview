from django.test import TestCase
from api.models.ubbe_ml_regressors import UbbeMlRegressors


class UbbeMlRegressorsTests(TestCase):
    """
    Tests the regressor model is functioning.
    Tests against present set of default values.
    """
    def setUp(self) -> None:
        regressors = UbbeMlRegressors()
        regressors.save()
        self.regressors = regressors

    def test(self):
        self.assertIsInstance(self.regressors, UbbeMlRegressors)
        self.assertIsInstance(self.regressors.pk, int)
        self.assertEqual(self.regressors.created_at.date(), self.regressors.modified_at.date())
        self.assertEqual(self.regressors.lbs_0_500_m, 0.0231)
        self.assertEqual(self.regressors.lbs_0_500_b, 26.6948)
        self.assertEqual(self.regressors.lbs_500_1000_m, 0.0135)
        self.assertEqual(self.regressors.lbs_500_1000_b, 17.7579)
        self.assertEqual(self.regressors.lbs_1000_2000_m, 0.0117)
        self.assertEqual(self.regressors.lbs_1000_2000_b, 13.4614)
        self.assertEqual(self.regressors.lbs_2000_5000_m, 0.0129)
        self.assertEqual(self.regressors.lbs_2000_5000_b, 11.9797)
        self.assertEqual(self.regressors.lbs_5000_10000_m, 0.0109)
        self.assertEqual(self.regressors.lbs_5000_10000_b, 9.8540)
        self.assertEqual(self.regressors.lbs_10000_plus_m, 0.0090)
        self.assertEqual(self.regressors.lbs_10000_plus_b, 9.285)
        self.assertEqual(self.regressors.min_price_m, 0.0516)
        self.assertEqual(self.regressors.min_price_b, 51.49)
        self.assertEqual('True, 51.49', self.regressors.__str__())
