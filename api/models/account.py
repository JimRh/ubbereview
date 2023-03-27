"""
    Title: Account Model
    Description: This file will contain functions for Account Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField
from django.db.models.fields.related import OneToOneField, ManyToManyField

from api.globals.project import BASE_TEN, PERCENTAGE_PRECISION
from api.models import Carrier
from api.models.base_table import BaseTable


class Account(BaseTable):
    """
        Account Model
    """

    _sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))
    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    user = OneToOneField(User, on_delete=CASCADE, related_name='groups_user')
    carrier = ManyToManyField(Carrier, related_name='groups_carrier')
    subaccounts_allowed = BooleanField(default=False)

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["user"]

    @classmethod
    def create(cls, param_dict: dict = None) -> 'Account':
        """
            Create Account from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Account Object
        """

        account = cls()
        if param_dict is not None:
            account.set_values(param_dict)
            account.user = param_dict.get("user")
        return account

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Account ({self.user.username}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.user.username}"
