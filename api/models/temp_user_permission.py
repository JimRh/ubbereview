"""
    Title: TEMP User Tier Modal
    Description: This file will contain functions for User Tier Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE
from django.db.models.fields.related import OneToOneField, ForeignKey

from api.globals.project import BASE_TEN, PERCENTAGE_PRECISION
from api.models import AccountTier
from api.models.base_table import BaseTable


class UserTier(BaseTable):
    """
        User Tier Model
    """

    _sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))
    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    user = OneToOneField(User, on_delete=CASCADE, related_name='user_user_tier')
    tier = ForeignKey(AccountTier, on_delete=CASCADE, related_name='user_tier', null=True, blank=True)

    class Meta:
        verbose_name = "User Tier"
        verbose_name_plural = "User Tiers"
        ordering = ["user"]

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< UserTier ({self.user.username}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.user.username}"
