"""
    Title: Action Express Order Price Modifiers
    Description: This file will contain helper functions related to Action Express Order Price Modifiers.
    Created: Sept 08, 2021
    Author: Carmichael
    Edited By:
    Edited Date:

    Rate Choices
        Edmonton to Edmonton? not a option with current pricing found.

        (1) BBE To & From Edmonton
        (2) BBE To & From Nisku / Leduc
        (3) - Acheson, Beaumont, Devon
        (4) - Calmar, Millet, Ft. Sask
        6. Hot Shot - Does not work

    Options:
        12:00 Add Rush
        1:30 Add Double Rush
        2:30 Add Direct (Taxi)
        5:30 Add After Hours (5:30 pm - 7:30 am)

    Once, 3:00 occurs add Action Express Option for next day plus Action Express Option with correct rush charge.

"""
import copy
import datetime
from decimal import Decimal

import pytz

from api.exceptions.project import RateExceptionNoEmail, ShipException


class PriceModifier:
    """
    Action Express Price Modifier for Order
    """

    def __init__(self, order: dict) -> None:
        self._order = order
        self._requests = []

    # (1) BBE To & From Edmonton
    # Routes: Edmonton
    _bbe_to_from_edmonton = {
        "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
        "Name": "BBE To & From Edmonton Area",
    }

    _bbe_tf_edmonton_cities = [
        "edmonton:edmontoninternationalairport",
        "edmontoninternationalairport:edmonton",
        "leduc:edmonton",
        "edmonton:leduc",
        "nisku:edmonton",
        "edmonton:nisku",
    ]

    # (2) BBE To & From Nisku / Leduc
    # Routes: Nisku, Leduc + Edmonton to Edmonton
    _bbe_to_from_nisku_leduc = {
        "ID": "5df4304d-e403-445f-9db4-42e1160b6b0b",
        "Name": "BBE To & From Nisku / Leduc",
    }

    _bbe_tf_nisku_leduc_cities = [
        "edmonton:edmonton",
        "edmontoninternationalairport:leduc",
        "leduc:edmontoninternationalairport",
        "nisku:nisku",
        "leduc:leduc",
        "leduc:nisku",
        "nisku:leduc",
        "edmontoninternationalairport:nisku",
        "nisku:edmontoninternationalairport",
    ]

    # (3) - Acheson, Beaumont, Devon
    # Routes: Acheson, Beaumont, Devon, Sherwood Park, St Albert, Winterburn
    _bbe_to_from_surrounding_areas_one = {
        "ID": "8f7d0753-767e-4205-9032-80b50bd2a269",
        "Name": "BBE To & From Surrounding Area #1",
    }

    _bbe_tf_sa_one_cities = [
        "edmontoninternationalairport:acheson",
        "acheson:edmontoninternationalairport",
        "edmontoninternationalairport:beaumont",
        "beaumont:edmontoninternationalairport",
        "edmontoninternationalairport:devon",
        "devon:edmontoninternationalairport",
        "edmontoninternationalairport:sherwoodpark",
        "sherwoodpark:edmontoninternationalairport",
        "edmontoninternationalairport:stalbert",
        "stalbert:edmontoninternationalairport",
        "edmontoninternationalairport:winterburn",
        "winterburn:edmontoninternationalairport",
        "edmonton:devon",
        "devon:edmonton",
    ]

    # (4) - Calmar, Millet, Ft. Sask
    # Routes: Calmar, Millet, Fort Saskatchewan, Enoch, Namao, Oliver, Spurce Grove, Stony Plain
    _bbe_to_from_surrounding_areas_two = {
        "ID": "241d3d73-0b0a-4237-8c06-487d5ddbd2e5",
        "Name": "BBE To & From Surrounding Area #2",
    }

    _bbe_tf_sa_two_cities = [
        "edmontoninternationalairport:calmar",
        "calmar:edmontoninternationalairport",
        "edmontoninternationalairport:millet",
        "millet:edmontoninternationalairport",
        "edmontoninternationalairport:fortsaskatchewan",
        "fortsaskatchewan:edmontoninternationalairport",
        "edmontoninternationalairport:enoch",
        "enoch:edmontoninternationalairport",
        "edmontoninternationalairport:namao",
        "namao:edmontoninternationalairport",
        "edmontoninternationalairport:oliver",
        "oliver:edmontoninternationalairport",
        "edmontoninternationalairport:sprucegrove",
        "sprucegrove:edmontoninternationalairport",
        "edmontoninternationalairport:stonyplain",
        "stonyplain:edmontoninternationalairport",
    ]

    #####

    _rush = {
        "ID": "7285893c-2f1d-4ede-bb46-03c95c31ab27",
        "Name": "(1) Rush (Nisku)",
        "Price": 18.0,
    }

    _double_rush = {
        "ID": "023e6428-04b5-41f6-b0db-1b10873af24b",
        "Name": "(2) Double Rush (Nisku)",
        "Price": 36.0,
    }

    _direct_rush = {
        "ID": "d7452d59-e971-4b8f-a02e-6d33e0e1068e",
        "Name": "(3) Direct Rush (Nisku)",
        "Price": 54.0,
    }

    _after_hours = {
        "ID": "06061c6e-1152-4696-b1f1-551cb61153ec",
        "Name": "(A10) After Hours (Nisku)",
        "Price": 80.0,
    }

    @staticmethod
    def _get_america_edmonton_time() -> str:
        """
        Get current time for america edmonton which is where action express is based.
        :return: formatted military time
        """
        tz = pytz.timezone("America/Edmonton")
        date = datetime.datetime.now(tz)

        return date.strftime("%H:%M")

    def _get_price_modifier(self, route: str) -> dict:
        """
        Get price modifier to add to shipment for correct pricing.
        :return:
        """

        if route in self._bbe_tf_edmonton_cities:
            return self._bbe_to_from_edmonton
        elif route in self._bbe_tf_nisku_leduc_cities:
            return self._bbe_to_from_nisku_leduc
        elif route in self._bbe_tf_sa_one_cities:
            return self._bbe_to_from_surrounding_areas_one
        elif route in self._bbe_tf_sa_two_cities:
            return self._bbe_to_from_surrounding_areas_two

        return {}

    def _get_rush_option(self, time: str) -> tuple:
        """

        Options:
            12:00 Add Rush
            1:30 Add Double Rush
            2:30 Add Direct (Taxi)
            5:30 Add After Hours (5:30 pm - 7:30 am)

        :return:
        """

        if "12:00" <= time <= "13:29":
            return self._rush, "RUSH:Rush", Decimal(self._rush["Price"])
        elif "13:30" <= time <= "14:29":
            return (
                self._double_rush,
                "DOUBLE:Double Rush",
                Decimal(self._double_rush["Price"]),
            )
        elif "14:30" <= time <= "17:30":
            return (
                self._direct_rush,
                "DIRECT:Direct Rush",
                Decimal(self._direct_rush["Price"]),
            )

        return {}, "", Decimal("0.00")

    def _get_rush_option_by_code(self, code: str) -> tuple:
        """

        Options:
            12:00 Add Rush
            1:30 Add Double Rush
            2:30 Add Direct (Taxi)
            5:30 Add After Hours (5:30 pm - 7:30 am)

        :return:
        """

        if code == "RUSH":
            return self._rush, "RUSH:Rush", Decimal(self._rush["Price"])
        elif code == "DOUBLE":
            return (
                self._double_rush,
                "DOUBLE:Double Rush",
                Decimal(self._double_rush["Price"]),
            )
        elif code == "DIRECT":
            return (
                self._direct_rush,
                "DIRECT:Direct Rush",
                Decimal(self._direct_rush["Price"]),
            )

        return {}, "", ""

    def add_rate_modifiers(self) -> list:
        """

        :return:
        """
        origin = self._order["CollectionLocation"]["City"].lower().replace(" ", "")
        destination = self._order["DeliveryLocation"]["City"].lower().replace(" ", "")
        route = f"{origin}:{destination}"
        time = self._get_america_edmonton_time()
        price = self._get_price_modifier(route=route)

        if not price:
            raise RateExceptionNoEmail(
                code="27104",
                message="AE PriceModifier (L206): No Price Found.",
                errors=[],
            )

        self._order["PriceModifiers"].append(price)

        if time < "12:00":
            return [(self._order, "REG:Regular", Decimal("0.00"))]

        copied = copy.deepcopy(self._order)
        rush_price, service, service_cost = self._get_rush_option(time=time)

        if not rush_price:
            return [(self._order, "REG:Regular", Decimal("0.00"))]

        copied["PriceModifiers"].append(rush_price)

        return [
            (self._order, "REG:Regular", Decimal("0.00")),
            (copied, service, service_cost),
        ]

    def add_ship_modifiers(self, service_code: str):
        """

        :return:
        """

        origin = self._order["CollectionLocation"]["City"].lower().replace(" ", "")
        destination = self._order["DeliveryLocation"]["City"].lower().replace(" ", "")
        route = f"{origin}:{destination}"
        price = self._get_price_modifier(route=route)

        if not price:
            raise ShipException("AE PriceModifier (L206): No Price Found.")

        self._order["PriceModifiers"].append(price)

        if service_code == "REG":
            return self._order, "REG:Regular", Decimal("0.00")

        rush_price, service, service_cost = self._get_rush_option_by_code(
            code=service_code
        )

        self._order["PriceModifiers"].append(rush_price)

        return self._order, service, service_cost
