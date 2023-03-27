"""
    Title: Account Tier Model
    Description: This file will contain functions for Account Tier Model.
    Created: February 14, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models import CharField, DecimalField, PositiveIntegerField, ManyToManyField

from api.globals.project import DEFAULT_CHAR_LEN, API_ZERO, PRICE_PRECISION, MAX_PRICE_DIGITS
from api.models import ApiPermissions
from api.models.base_table import BaseTable

# TODO - Rework Additional fields/


class AccountTier(BaseTable):
    """
        Account Tier Model
    """

    name = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Name of tier.")
    code = CharField(max_length=DEFAULT_CHAR_LEN, help_text="code for tier.")
    base_cost = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Tier base cost.")
    user_cost = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Cost of users allowed for tier."
    )
    shipment_cost = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Cost of shipments allowed for tier."
    )
    carrier_cost = DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="Cost of carriers accounts allowed for tier."
    )
    api_requests_per_minute_cost = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Cost of requests allowed for tier."
    )
    user_count = PositiveIntegerField(help_text="Number of users allowed for tier.")
    shipment_count = PositiveIntegerField(help_text="Number of shipments allowed for tier.")
    carrier_count = PositiveIntegerField(default=API_ZERO, help_text="Number of carriers accounts allowed for tier.")
    api_requests_per_minute_count = PositiveIntegerField(help_text="Number of requests allowed for tier.")
    additional_user_count = PositiveIntegerField(
        default=API_ZERO, help_text="Number of additional users to charge for."
    )
    additional_shipment_count = PositiveIntegerField(
        default=API_ZERO, help_text="Number of additional shipments to charge for."
    )
    additional_carrier_count = PositiveIntegerField(
        default=API_ZERO, help_text="Number of additional carriers accounts to charge for."
    )
    additional_api_requests_count = PositiveIntegerField(
        default=API_ZERO, help_text="Number of additional requests to charge for."
    )

    permissions = ManyToManyField(
        ApiPermissions, related_name='tier_permissions', help_text="Api Endpoints the tier has access to."
    )

    class Meta:
        verbose_name = "AccountTier"
        verbose_name_plural = "Account - Tier's"

    def save(self, *args, **kwargs) -> None:

        if not self.code:
            self.code = self.name.strip().lower().replace(" ", "_")

        self.clean_fields()
        super().save(*args, **kwargs)

    def __repr__(self):
        return f'< AccountTier(name={self.name}, base_cost={self.base_cost}) >'

    def __str__(self):
        return f'{self.name}'
