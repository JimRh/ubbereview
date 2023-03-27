"""
    Title: Pickup Validate
    Description: This file will contain all functions that will validate carrier pickup request. If no carrier specific
                 pickup validation exists, defaults will be used.
    Created: August 17, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from pytz import UTC

from api.apis.exchange_rate.endpoints.exchange_rate_api import OpenExchangeRateApi
from api.exceptions.project import ViewException
from api.models import ExchangeRate
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ExchangeRateUtility:
    _sig_fig = Decimal("0.000001")

    def __init__(self, source_currency: str, target_currency: str):
        self._source_currency = source_currency
        self._target_currency = target_currency

    def _get_currency(self) -> Decimal:
        """

            :return:
        """

        exchange_rate = OpenExchangeRateApi(
            source=self._source_currency, target=self._target_currency
        ).get_exchange_rate()

        return exchange_rate.quantize(self._sig_fig)

    def _get_exchange_rate(self):
        """

            :return:
        """

        try:
            exchange_rate = ExchangeRate.objects.get(
                source_currency=self._source_currency, target_currency=self._target_currency
            )
        except ObjectDoesNotExist:
            exchange_rate = self._save_currency(exchange_rate=self._get_currency())

        if datetime.datetime.now(tz=UTC) > exchange_rate.expire_date:
            exchange_rate.exchange_rate = self._get_currency()
            exchange_rate.save()

        return exchange_rate.exchange_rate

    def _save_currency(self, exchange_rate: Decimal):
        """

            :param exchange_rate:
            :return:
        """

        try:
            exchange_rate = ExchangeRate.create(param_dict={
                "source_currency": self._source_currency,
                "target_currency": self._target_currency,
                "exchange_rate": exchange_rate,
            })
            exchange_rate.save()
        except ValidationError as e:
            errors = [{x: y} for x, y in e.message_dict.items()]
            raise ViewException(code="9005", message=f"ExchangeRate: Failed to create new.", errors=errors)

        return exchange_rate

    def get_exchange_rate(self) -> Decimal:
        """

            :return:
        """
        lookup_key = f"{self._source_currency}_to_{self._target_currency}"
        exchange_rate = cache.get(lookup_key)

        if not exchange_rate:
            exchange_rate = self._get_exchange_rate()
            cache.set(lookup_key, exchange_rate, TWENTY_FOUR_HOURS_CACHE_TTL)

        return exchange_rate
