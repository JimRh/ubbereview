"""
    Title: BBE Base Api
    Description: This file will contain functions related to BBE base Api.
    Created: July 13, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist

from api.globals.carriers import BBE
from api.models import FuelSurcharge, BBELane


class BBEAPI:
    """
    Class will handle common details between the sub classes.
    """

    _hundred = Decimal("100.00")
    _thousand = Decimal("1000.00")
    _cubic = Decimal("2.5")
    _sig_fig = Decimal("0.01")
    _zero = Decimal("0.00")

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._carrier_id = self._ubbe_request["carrier_id"]

    def _get_freight_cost(self, sheet: BBELane, weight: Decimal) -> Decimal:
        """
        Function will return the freight cost for a given lane (Origin to Destination)
        :param sheet: BBE Lane
        :param weight: Total Weight of the shipment
        :return: Freight Cost (Decimal)
        """

        if weight < sheet.weight_break:
            return sheet.minimum_charge.quantize(self._sig_fig)

        # Calculate Remaining weight and times it by the price per
        cost = (weight - sheet.weight_break) * sheet.price_per
        final = sheet.minimum_charge + cost

        return final.quantize(self._sig_fig)

    def _get_fuel_surcharge_cost(
        self, final_weight: Decimal, freight_cost: Decimal
    ) -> dict:
        """
        Function will return the fuel surcharge for a given lane
        :param freight_cost: Freight cost of the lane
        :return: Fuel Surcharge dictionary
        """

        if self._origin["country"] == self._destination["country"]:
            fuel_type = "D"
        else:
            fuel_type = "I"

        try:
            fuel_surcharge = FuelSurcharge.objects.get(
                carrier__code=BBE, fuel_type=fuel_type
            )
        except ObjectDoesNotExist:
            cost = {
                "name": "Fuel Surcharge",
                "cost": Decimal("0.00"),
                "percentage": Decimal("0.00"),
            }
        else:
            cost = fuel_surcharge.get_json(
                weight=final_weight, freight_cost=freight_cost
            )

        return cost

    def get_rate_sheet_rate(self):
        """
        Gets a Rate Sheet for BBE
        :return: None or Rate Sheet Object
        """

        try:
            rate_sheet = BBELane.objects.select_related("carrier").get(
                origin_postal_code=self._origin["postal_code"].replace(" ", "").upper(),
                origin_province__code=self._origin["province"],
                destination_postal_code=self._destination["postal_code"]
                .replace(" ", "")
                .upper(),
                destination_province__code=self._destination["province"],
                carrier__code=BBE,
            )

        except ObjectDoesNotExist:
            return None

        return rate_sheet

    def get_rate_sheet_ship(self):
        """
        Gets a Rate Sheet for BBE
        :return: None or Rate Sheet Object
        """

        try:
            rate_sheet = BBELane.objects.get(
                origin_postal_code=self._origin.get("postal_code", "")
                .replace(" ", "")
                .upper(),
                origin_province__code=self._origin["province"],
                destination_postal_code=self._destination.get("postal_code", "")
                .replace(" ", "")
                .upper(),
                destination_province__code=self._destination["province"],
                carrier__code=BBE,
                service_code=self._ubbe_request["service_code"],
            )
        except ObjectDoesNotExist:
            return None

        return rate_sheet
