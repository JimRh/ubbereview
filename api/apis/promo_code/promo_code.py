"""
    Title: Promo Code Utility
    Description: This file will contain utility functions for Promo code.
    Created: June 09, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import utc

from api.exceptions.project import ViewException
from api.globals.project import BASE_TEN, PRICE_PRECISION
from api.models import PromoCode


class PromoCodeUtility:
    _hundred = Decimal("100.0")
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    @staticmethod
    def _get_promo_code(promo_code: str) -> PromoCode:
        """
            Get promo code Object.
            :param promo_code: Promo Code Value
            :return: PromoCode Object
        """

        try:
            promo = PromoCode.objects.get(code=promo_code)
        except ObjectDoesNotExist:
            errors = [{"promo_code": f"Not found 'code': {promo_code}."}]
            raise ViewException(code="3510", message=f"PromoCode: '{promo_code}.' not found.", errors=errors)

        return promo

    @staticmethod
    def validate_promo_code(promo_code: PromoCode) -> None:
        """
            Validate the promo code to ensure its active and meets the criteria.
            :param promo_code: Promo Code Object.
            :return:
        """
        errors = []

        if not promo_code.is_active:
            errors.append({"promo_code": "PromoCode Invalid: Not Active"})
            raise ViewException(code="X", message="PromoCode Invalid: Not Active", errors=errors)

        if promo_code.start_date and promo_code.end_date:
            now = datetime.datetime.now().replace(tzinfo=utc)

            if not (promo_code.start_date <= now <= promo_code.end_date):
                message = "PromoCode Invalid: Not valid for current date."
                errors.append({"promo_code": message})
                raise ViewException(code="X", message=message, errors=errors)

        if promo_code.quantity == 0:
            message = f"PromoCode Invalid: {promo_code.code} has no more uses remaining"
            errors.append({"promo_code": message})
            raise ViewException(code="X", message=message, errors=errors)

    def flat_promo_code(self, promo_code: PromoCode, pre_tax_cost: Decimal) -> Decimal:
        """
            Get Flat Promo Code Discount.
            :return:
        """
        errors = []

        if pre_tax_cost < promo_code.min_shipment_cost:
            errors.append({"promo_code": f"Min Cost of {promo_code.min_shipment_cost} required."})
            raise ViewException(
                code="X", message=f"Min Cost of {promo_code.min_shipment_cost} required.", errors=errors
            )

        return Decimal(promo_code.flat_amount).quantize(self._price_sig_fig)

    def percentage_promo_code(self, promo_code: PromoCode, pre_tax_cost: Decimal) -> Decimal:
        """
            Get Percentage Promo Code Discount.
            :return:
        """
        errors = []

        if pre_tax_cost < promo_code.min_shipment_cost:
            errors.append({"promo_code": "Min Cost of {promo_code.min_shipment_cost} required."})
            raise ViewException(code="X", message=f"Min Cost of {promo_code.min_shipment_cost} required.", errors=errors)

        reduction_amount = pre_tax_cost * (promo_code.percentage / self._hundred)

        if reduction_amount >= promo_code.max_discount:
            discount = promo_code.max_discount
        else:
            discount = reduction_amount

        return Decimal(discount).quantize(self._price_sig_fig)

    def apply(self, promo_code: str, pre_tax_cost: Decimal) -> Decimal:
        """

            :param promo_code:
            :param pre_tax_cost:
            :return:
        """

        promo_code = self._get_promo_code(promo_code=promo_code)

        self.validate_promo_code(promo_code=promo_code)

        if promo_code.flat_amount == Decimal("0.00"):
            discount = self.percentage_promo_code(promo_code=promo_code, pre_tax_cost=pre_tax_cost)
        else:
            discount = self.flat_promo_code(promo_code=promo_code, pre_tax_cost=pre_tax_cost)

        promo_code.quantity -= 1
        promo_code.save()

        return discount

    def get_discount(self, data: dict) -> dict:
        """
            Get Discount amount for promo code.
            :param data: Promo Code data containing code and pre tax shipment cost.
            :return:
        """

        promo_code = self._get_promo_code(promo_code=data["promo_code"])

        self.validate_promo_code(promo_code=promo_code)

        if promo_code.flat_amount == Decimal("0.00"):
            discount = self.percentage_promo_code(promo_code=promo_code, pre_tax_cost=data["pre_tax_cost"])
        else:
            discount = self.flat_promo_code(promo_code=promo_code, pre_tax_cost=data["pre_tax_cost"])

        return {
            "promo_code": promo_code.code,
            "discount": discount,
            "is_valid": True
        }
