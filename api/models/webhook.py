"""
    Title: Webhook Model
    Description: This file will contain functions for webhooks Model.
    Created: July 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db.models.deletion import PROTECT
from django.db.models.fields import CharField, URLField
from django.db.models.fields.related import ForeignKey

from api.globals.project import MAX_CHAR_LEN, LETTER_MAPPING_LEN
from api.models import SubAccount
from api.models.base_table import BaseTable


class Webhook(BaseTable):

    _EVENTS = (
        ("TSC", "Tracking Status Change"),
    )

    _FORMAT = (
        ("JSO", "Json"),
        ("XML", "XML"),
    )

    sub_account = ForeignKey(SubAccount, on_delete=PROTECT, help_text="The account the webhook belongs to.")
    event = CharField(max_length=LETTER_MAPPING_LEN * 3, choices=_EVENTS, help_text="The webhook event to perform.")
    url = URLField(max_length=MAX_CHAR_LEN,help_text="The url to post the event data to.")
    data_format = CharField(max_length=LETTER_MAPPING_LEN * 3, choices=_FORMAT, help_text="Data Format")

    class Meta:
        verbose_name = "Webhook"
        verbose_name_plural = "Webhook's"

    # Override
    def __repr__(self) -> str:
        return f"< Webhook ({repr(self.sub_account)}: {self.event}, {self.url}, {self.data_format}) >"

    # Override
    def __str__(self) -> str:
        return f"{str(self.sub_account)}: {self.event}, {self.url}, {self.data_format}"
