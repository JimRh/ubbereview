from api.models.base_table import BaseTable
from django.db import models


class UbbeMlRegressors(BaseTable):
    """
    These are the numbers used to predict the price
    The (lbs) weight bins are:
    {[0, 501),[501,1001),[1001,2001),[2001,5001),[5001,10001),[10001,+inf)}
    The units of the binned regressors is Canadian Dollars.
    """
    # Only one set of regressors can be active
    active = models.BooleanField(default=True, unique=True, help_text="Unique and defaults to True")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    lbs_0_500_m = models.FloatField(default=0.0231, help_text="Rate per 100lbs*km from 0. km to 500 - slope(m).")
    lbs_0_500_b = models.FloatField(default=26.6948, help_text="Rate per 100lbs*km from 0. km to 500 - intercept(b).")

    lbs_500_1000_m = models.FloatField(default=0.0135,  help_text="Rate per 100lbs*km from 501. km to 1000 km - slope(m).")
    lbs_500_1000_b = models.FloatField(default=17.7579,  help_text="Rate per 100lbs*km from 501. km to 1000 km - intercept(b).")

    lbs_1000_2000_m = models.FloatField(default=0.0117, help_text="Rate per 100lbs*km from 1001. km to 2000 km - slope(m).")
    lbs_1000_2000_b = models.FloatField(default=13.4614, help_text="Rate per 100lbs*km from 1001. km to 2000 km - intercept(b).")

    lbs_2000_5000_m = models.FloatField(default=0.0129, help_text="Rate per 100lbs*km from 2001. km to 5000 km - slope(m).")
    lbs_2000_5000_b = models.FloatField(default=11.9797, help_text="Rate per 100lbs*km from 2001. km to 5000 km - intercept(b).")

    lbs_5000_10000_m = models.FloatField(default=0.0109, help_text="Rate per 100lbs*km from 5001. km to 10000 km - slope(m).")
    lbs_5000_10000_b = models.FloatField(default=9.8540, help_text="Rate per 100lbs*km from 5001. km to 10000 km - intercept(b).")

    lbs_10000_plus_m = models.FloatField(default=0.0090, help_text="Rate per 100lbs*km from over 10001 km - slope(m).")
    lbs_10000_plus_b = models.FloatField(default=9.285, help_text="Rate per 100lbs*km from over 10001 km - intercept(b).")

    min_price_m = models.FloatField(default=0.0516, help_text="Minimum price predictor - slope(m)")
    min_price_b = models.FloatField(default=51.49, help_text="Minimum price predictor")

    class Meta:
        verbose_name = "ubbeML"
        verbose_name_plural = "ubbeML"

    # Override
    def __repr__(self) -> str:
        return f"< UbbeMlRegressors ({self.active}, {self.min_price_b}, {self.modified_at}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.active}, {self.min_price_b}"
