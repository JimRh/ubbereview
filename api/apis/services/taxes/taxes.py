import datetime
from datetime import timedelta
from decimal import Decimal
from typing import Dict

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.utils import timezone

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import Tax, Province, API
from brain.settings import TAXJAR_API_KEY


class Taxes:
    # TODO - REVIEW INTERNATIONAL TAX, VERY BROKEN FOR NON US AND CA
    _tax_date_cutoff = 12  # 3 months

    def __init__(self, location: dict) -> None:
        self._province = location["province"]
        self._country = location["country"]
        self._postal_code = location["postal_code"]
        self._city = location["city"]

    @staticmethod
    def _fetch_tax_rate(params: Dict[str, str]) -> Decimal:
        header = {'Authorization': 'Bearer ' + TAXJAR_API_KEY}
        url = "https://api.taxjar.com/v2/rates/?zip={}&country={}&state={}&city={}".format(params["zip"],
                                                                                           params["country"],
                                                                                           params["state"],
                                                                                           params["city"])

        try:
            response = requests.get(url, headers=header, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException:
            raise RequestError()

        try:
            response.raise_for_status()
        except requests.RequestException:
            raise RequestError(response, params)

        try:
            new_response = response.json()
        except ValueError:
            raise RequestError(response, params)

        rate = new_response["rate"].get("combined_rate", "")

        if not rate:
            rate = new_response["rate"].get("standard_rate", "")

        return Decimal(rate) * Decimal("100.00")

    @staticmethod
    def _is_tax_rate_expired(expiry: datetime) -> bool:
        return timezone.now() > expiry

    def _update_tax_rate(self, tax: Tax) -> Tax:
        params = {
            "zip": self._postal_code,
            "country": self._country,
            "state": self._province,
            "city": self._city
        }
        rate = self._fetch_tax_rate(params)

        tax.tax_rate = rate
        tax.expiry = timezone.now() + timedelta(weeks=self._tax_date_cutoff)
        tax.save()
        return tax

    def get_tax_rate(self, amount: Decimal) -> Decimal:
        if not API.objects.get(name="TaxJar").active:
            connection.close()
            return Decimal("0.00")

        try:
            province = Province.objects.get(code=self._province, country__code=self._country)
        except ObjectDoesNotExist:
            CeleryLogger().l_error.delay(
                location="taxes.py line: 77",
                message=str(
                    {"api.error.tax": "Province object with province code {} and country code {} could not be found".format(self._province, self._country)
            }))
            return Decimal("0.00")

        try:
            tax = Tax.objects.get(province=province)
        except ObjectDoesNotExist:
            tax = Tax()
            tax.province = province
            tax.expiry = timezone.now() - timedelta(days=1)

        if self._is_tax_rate_expired(tax.expiry):
            tax = self._update_tax_rate(tax)
        return (tax.tax_rate * amount / Decimal("100.00")).quantize(Decimal("0.01"))

    def get_tax(self) -> Tax:
        if not API.objects.get(name="TaxJar").active:
            connection.close()
            raise Exception

        try:
            province = Province.objects.get(code=self._province, country__code=self._country)
        except ObjectDoesNotExist:
            CeleryLogger().l_error.delay(
                location="taxes.py line: 77",
                message=str(
                    {"api.error.tax": "Province object with province code {} and country code {} could not be found".format(self._province, self._country)
            }))
            raise Exception

        try:
            tax = Tax.objects.get(province=province)
        except ObjectDoesNotExist:
            tax = Tax()
            tax.province = province
            tax.expiry = timezone.now() - timedelta(days=1)

        if self._is_tax_rate_expired(tax.expiry):
            tax = self._update_tax_rate(tax)

        return tax
