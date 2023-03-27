"""
    Title: Rate Log Model
    Description: This file will contain functions for Rate Log Model.
    Created: April 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import uuid

from django.db.models import JSONField, BooleanField
from django.db.models.deletion import PROTECT
from django.db.models.fields import DateTimeField, CharField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_KEY_LENGTH, SHIPMENT_IDENTIFIER_LEN
from api.models import SubAccount
from api.models.base_table import BaseTable


class RateLog(BaseTable):

    rate_date = DateTimeField(auto_now_add=True, editable=True, help_text="Date of rate request.")

    rate_log_id = CharField(
        max_length=DEFAULT_KEY_LENGTH,
        help_text="Rate Log UUID to tie Rate to Ship.",
    )
    shipment_id = CharField(
        max_length=SHIPMENT_IDENTIFIER_LEN,
        help_text="The internal GO shipping identifier for the shipment",
        default="",
        null=True,
        blank=True
    )
    sub_account = ForeignKey(SubAccount, on_delete=PROTECT, help_text="Account for rate request.")
    rate_data = JSONField(default=dict, help_text="Rate Request Data.")
    ship_data = JSONField(default=dict, help_text="Rate Request Data.", null=True, blank=True)
    response_data = JSONField(default=dict, help_text="Rate Response Data.", null=True, blank=True)
    is_no_rate = BooleanField(default=False, help_text="Does the rate log have rates returned.")

    class Meta:
        verbose_name = "Rate Log"
        verbose_name_plural = "Rate Logs"

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create RateLog from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: RateLog Object
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.sub_account = param_dict.get('sub_account')
        return obj

    # Override
    def save(self, *args, **kwargs) -> None:

        if not self.rate_log_id:
            rate_log_id = uuid.uuid4()

            while RateLog.objects.filter(rate_log_id=rate_log_id).exists():
                rate_log_id = uuid.uuid4()

            self.rate_log_id = str(rate_log_id)

        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< RateLog ({self.rate_date.isoformat()}: {repr(self.sub_account)}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.rate_date.isoformat()}: {self.sub_account}"
