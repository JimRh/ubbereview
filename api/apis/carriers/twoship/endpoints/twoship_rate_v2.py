"""
    Title: 2Ship Rate api
    Description: This file will contain functions related to 2Ship rate Api.
    Created: January 10, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal, ROUND_UP

import gevent
from django.db import connection

from api.apis.carriers.twoship.endpoints.twoship_base_v2 import TwoShipBase
from api.exceptions.project import RateException, RequestError, ViewException
from api.models import CityNameAlias


class TwoShipRate(TwoShipBase):
    """
    Two Ship Rate Class
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._requests = []
        self._responses = []
        self._carriers = self._ubbe_request["carrier_id"]

    @staticmethod
    def _build_address(address: dict, carrier_id: int) -> dict:
        """
        Format address into 2Ship version and check for city alias for carrier
        :param address: Address Dict
        :param carrier_id: Carrier ID
        :return: 2Ship Address Dict
        """

        city = CityNameAlias.check_alias(
            alias=address["city"].lower(),
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=carrier_id,
        )

        return {
            "Address1": address["address"],
            "City": city,
            "CompanyName": address["company_name"],
            "Country": address["country"],
            "IsResidential": not address.get("has_shipping_bays", True),
            "PostalCode": address["postal_code"],
            "State": address["province"],
        }

    def _build_packages(self) -> list:
        """
        Build 2ship packages from ubbe packages.
        :return: 2Ship Package list
        """

        package_list = []

        for package in self._ubbe_request["packages"]:
            item = {
                "DimensionType": self._dimension_type_metric,
                "WeightType": self._weight_type_metric,
                "Length": package["length"].quantize(self._sig_fig, rounding=ROUND_UP),
                "Width": package["width"].quantize(self._sig_fig, rounding=ROUND_UP),
                "Height": package["height"].quantize(self._sig_fig, rounding=ROUND_UP),
                "Weight": package["weight"].quantize(self._sig_fig, rounding=ROUND_UP),
            }

            package_list += [item] * package["quantity"]

        return package_list

    def _build(self):
        """
        Build 2Ship Rate request for each carrier.
        :return:
        """

        for carrier in self._carriers:
            request = {
                "WS_Key": self._api_key,
                "LocationId": self._bbe_yeg_ff_location_id,
                "CarrierID": carrier,
                "Sender": self._build_address(
                    address=self._ubbe_request["origin"], carrier_id=carrier
                ),
                "Recipient": self._build_address(
                    address=self._ubbe_request["destination"], carrier_id=carrier
                ),
                "Packages": self._build_packages(),
                "ShipmentOptions": {"SignatureRequired": True},
                "PickupRequest": True,
                "InternationalOptions": {"Invoice": {"Currency": "CAD"}},
            }

            self._requests.append(copy.deepcopy(request))

    def _format_response(self) -> list:
        """
        Format 2Ship response into ubbe format.
        :return:
        """

        rates = []

        for rate in self._responses:

            carrier_name = rate["Carrier"]["Name"]
            carrier_id = rate["Carrier"]["Id"]

            for service_level in rate.get("Services", []):
                service = service_level["Service"]
                service_name = service.get("Name", "")
                service_id = service.get("Code", "")

                if not service_name or not service_id:
                    continue

                client_price = service_level.get("ClientPrice", {})

                if not client_price:
                    continue

                freight = Decimal(str(client_price["Freight"]))
                surcharges = Decimal(str(client_price["TotalSurcharges"]))
                fuel = Decimal(str(client_price["Fuel"]["Amount"]))
                tax_rate = self._get_total_of_key(client_price["Taxes"], "Percentage")
                tax_amount = Decimal(str(client_price["TotalTaxes"]))
                total = Decimal(str(client_price["TotalPriceInSelectedCurrency"]))

                ret = {
                    "carrier_id": carrier_id,
                    "carrier_name": carrier_name,
                    "service_code": service_id,
                    "service_name": service_name,
                    "freight": freight.quantize(self._sig_fig),
                    "surcharge": (surcharges + fuel).quantize(self._sig_fig),
                    "tax": tax_amount.quantize(self._sig_fig),
                    "tax_percent": tax_rate.quantize(self._sig_fig),
                    "total": total.quantize(self._sig_fig),
                    "transit_days": service_level.get("TransitDays", -1),
                    "delivery_date": service_level.get("DeliveryDate", ""),
                }

                rates.append(ret)

        return rates

    def _get_rates(self) -> None:
        rate_threads = [
            gevent.Greenlet.spawn(self._post, self._rate_url, r) for r in self._requests
        ]

        gevent.joinall(rate_threads)

        for rate_thread in rate_threads:
            try:
                rate_thread = rate_thread.get()
            except (RequestError, ViewException):
                continue

            if rate_thread["IsError"]:
                continue

            self._responses.extend(rate_thread["Data"])

    def rate(self) -> list:
        """
        Get rates for 2Ship based carriers.
        :return: list of dictionary rates
        """

        if self._ubbe_request.get("carrier_options", []):
            connection.close()
            raise RateException("2Ship Rate (L187): 2Ship Options not supported.")

        try:
            self._build()
        except RateException as e:
            connection.close()
            raise RateException(
                f"2Ship Rate (L198): Failed building request. {e.message}"
            ) from e

        try:
            self._get_rates()
        except RequestError as e:
            connection.close()
            raise RateException(
                f"2Ship Rate (L198): Failed building request. {str(e)}"
            ) from e

        try:
            rates = self._format_response()
        except RateException as e:
            connection.close()
            raise RateException(
                f"2Ship Rate (L198): Failed building request. {e.message}"
            ) from e

        connection.close()
        return rates
