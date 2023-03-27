"""
    Title: Option Abstract
    Description: This file will contain functions for Option Abstract.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db.models.fields import CharField, DecimalField, DateTimeField

from api.globals.project import DEFAULT_CHAR_LEN, MAX_PRICE_DIGITS, PRICE_PRECISION, PERCENTAGE_PRECISION, \
    MAX_PERCENTAGE_DIGITS, BASE_TEN
from api.models.base_table import BaseTable


class Option(BaseTable):
    """
        Option Abstract
    """

    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _percentage_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    evaluation_expression = CharField(max_length=DEFAULT_CHAR_LEN)
    minimum_value = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, default=Decimal("0.00"))
    maximum_value = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, default=Decimal("999999999999.99")
    )
    percentage = DecimalField(
        decimal_places=PERCENTAGE_PRECISION, max_digits=MAX_PERCENTAGE_DIGITS, default=Decimal("0.00")
    )
    start_date = DateTimeField(blank=True, null=True)
    end_date = DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
