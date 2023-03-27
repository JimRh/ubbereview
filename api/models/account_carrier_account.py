"""
    Title: CarrierAccount Model
    Description: This file will contain functions for CarrierAccount Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import CASCADE
from django.db.models.fields.related import ForeignKey, OneToOneField

from api.models import Carrier, EncryptedMessage
from api.models.base_table import BaseTable


class CarrierAccount(BaseTable):
    """
        CarrierAccount Model
    """

    carrier = ForeignKey(Carrier, on_delete=CASCADE, related_name='carrieraccount_carrier')
    subaccount = ForeignKey('SubAccount', on_delete=CASCADE, related_name='carrieraccount_subaccount')

    api_key = OneToOneField(
        EncryptedMessage,
        on_delete=CASCADE,
        related_name='carrieraccount_api_key',
        null=True,
        blank=True,
    )
    username = OneToOneField(
        EncryptedMessage,
        on_delete=CASCADE,
        related_name='carrieraccount_username',
        null=True,
        blank=True,
    )
    password = OneToOneField(
        EncryptedMessage,
        on_delete=CASCADE,
        related_name='carrieraccount_password',
        null=True,
        blank=True,
    )
    account_number = OneToOneField(
        EncryptedMessage,
        on_delete=CASCADE,
        related_name='carrieraccount_account_number',
        null=True,
        blank=True,
    )
    contract_number = OneToOneField(
        EncryptedMessage,
        on_delete=CASCADE,
        related_name='carrieraccount_contract_number',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "CarrierAccount"
        verbose_name_plural = "Account - Carrier Account's"

    def __repr__(self):
        return f'< CarrierAccount(subaccount={self.subaccount}, carrier={self.carrier}) >'

    def __str__(self):
        return f'{self.subaccount}, {self.carrier}'
