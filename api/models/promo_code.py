"""
    Title: PromoCode DB Table
    Description: This file will contain the PromoCode model for the database.
    Created: June 06, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import random
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import IntegerField, DateTimeField, CharField, DecimalField, BooleanField

from api.globals.project import DEFAULT_CHAR_LEN, MAX_PRICE_DIGITS, PRICE_PRECISION, PERCENTAGE_PRECISION, \
    MAX_PERCENTAGE_DIGITS, GO_PREFIX
from api.models.base_table import BaseTable


class PromoCode(BaseTable):
    # PretaxTotal - PromoAmount = Sub-Total + tax = Total - Leah
    code = CharField(max_length=DEFAULT_CHAR_LEN, unique=True)
    start_date = DateTimeField(null=True, blank=True)
    end_date = DateTimeField(null=True, blank=True)
    quantity = IntegerField()
    flat_amount = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, default=Decimal('0.00'), help_text="Flat amount"
    )
    min_shipment_cost = DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        default=Decimal('0.00'),
        help_text="Minimum shipment cost to apply promo"
    )
    max_discount = DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        default=Decimal('0.00'),
        help_text="Max amount to apply percentage discount"
    )
    percentage = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        default=Decimal('0.00'),
        help_text="Percentage discount"
    )
    amount = IntegerField(
        default=0,
        help_text="Bulk create amount."
    )
    is_active = BooleanField(default=True, help_text='Is the promo code active?')
    is_bulk = BooleanField(default=False, help_text='Do you want to bulk create promo codes?')

    class Meta:
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"

    def clean(self) -> None:
        decimal_default = Decimal('0.00')
        errors = []

        if self.flat_amount != decimal_default:
            if self.percentage != decimal_default:
                errors.append("'flat_price' cannot exist with 'percentage'")
        else:
            if self.percentage == decimal_default:
                errors.append("'flat_price' or 'percentage' must be greater than '0.00'")

        if self.percentage != decimal_default:
            if self.max_discount == decimal_default:
                errors.append("'percentage' requires 'Max Discount'")
        else:
            if self.max_discount != decimal_default:
                errors.append("'Max Discount' requires 'percentage'")

        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                errors.append("'start_date' must occur before 'end_date'")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        if self.code == '':
            self.code = "{}{:06}".format(GO_PREFIX, random.randint(0, 999999))
            while PromoCode.objects.filter(code=self.code).count() == 1:
                self.code = "{}{:06}".format(GO_PREFIX, random.randint(0, 999999))

        self.code = self.code.upper()
        self.flat_amount = round(Decimal(self.flat_amount), PRICE_PRECISION)
        self.min_shipment_cost = round(Decimal(self.min_shipment_cost), PRICE_PRECISION)
        self.max_discount = round(Decimal(self.max_discount), PRICE_PRECISION)
        self.percentage = round(Decimal(self.percentage), PERCENTAGE_PRECISION)

        super().save()

    # Override
    def __repr__(self) -> str:
        return "{}: {}".format(self.code, self.quantity)

        # Override
    def __str__(self) -> str:
        return f"{str(self.code)}: {self.start_date}, {self.end_date}, {self.quantity}, {self.flat_amount}, {self.percentage},  {self.min_shipment_cost}, {self.max_discount}, {self.is_active}, {self.is_bulk} "
