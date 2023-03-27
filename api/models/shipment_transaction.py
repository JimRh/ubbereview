"""
    Title: Transaction Model Class
    Description: This file will contain the Transaction model for the database.
    Created: Jan  23, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, BooleanField, DateTimeField, DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import PRICE_PRECISION, MAX_PRICE_DIGITS, DEFAULT_CHAR_LEN, TRANSACTION_IDENTIFIER_LEN, \
    TRANSACTION_RESPONSE_LEN
from api.models.base_table import BaseTable


class Transaction(BaseTable):
    """
        Shipment Transaction
    """

    shipment = ForeignKey("Shipment", on_delete=CASCADE, related_name='transaction_shipment')
    transaction_date = DateTimeField(auto_now_add=True, help_text="Date of transaction.")
    payment_date = CharField(max_length=DEFAULT_CHAR_LEN, help_text="payment date from moneris", default="", blank=True)
    payment_time = CharField(max_length=DEFAULT_CHAR_LEN, help_text="payment time from moneris", default="", blank=True)
    transaction_id = CharField(
        max_length=TRANSACTION_IDENTIFIER_LEN, unique=True, blank=True, help_text="Transaction id from moneris"
    )
    transaction_number = CharField(max_length=TRANSACTION_RESPONSE_LEN, help_text="Transaction number from moneris")
    transaction_amount = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Amount paid by customer."
    )
    transaction_type = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="Transaction type from moneris", default="", blank=True
    )
    complete = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Complete from moneris", default="")
    card_type = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Card type from moneris", default="")
    code = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Response Code from moneris", default="", blank=True)
    message = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Message from moneris", default="", blank=True)
    auth_code = CharField(max_length=DEFAULT_CHAR_LEN, help_text="auth code from moneris", default="", blank=True)
    receipt_id = CharField(max_length=DEFAULT_CHAR_LEN, help_text="receipt id from moneris", default="", blank=True)
    iso = CharField(max_length=DEFAULT_CHAR_LEN, help_text="iso from moneris", default="", blank=True)
    is_pre_authorized = BooleanField(default=False, help_text="Amount paid by customer.")
    is_captured = BooleanField(default=False, help_text="Has payment been captured.")
    is_payment = BooleanField(default=False, help_text="Has payment been payment.")

    class Meta:
        verbose_name = "Shipment Transaction"
        verbose_name_plural = "Shipment - Transaction's"

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create Transaction from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: Transaction Object
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.shipment = param_dict.get('shipment')
        return obj

    # Override
    def __repr__(self) -> str:
        return f"< Transaction ({self.shipment.shipment_id}, {self.transaction_date}: {self.transaction_id}>"

    # Override
    def __str__(self) -> str:
        return f"{self.shipment.shipment_id}, {self.transaction_date}: {self.transaction_id}"
