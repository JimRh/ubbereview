"""
    Title: Calm Air Base Class
    Description: This file will contain common functions between Rate, Ship, and Track.
    Created: August 20, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
from decimal import Decimal

from api.globals.carriers import CALM_AIR

from brain.settings import DEBUG


class CalmAirBase:
    """
    Calm Air Base Class
    """

    _base_url = "https://cargo.calmair.com/API_Gateway"
    _carrier_name = "Calm Air"
    _sig_fig = Decimal("0.01")
    _zero = "0"

    _remove_services = ["C202"]

    _services_names = {
        "GEN": "General Shipments",
        "PRI": "Priority Shipments",
        "BBE": "Priority or Food Shipments",
        "BBEG": "GENERAL SHIPMENTS ONLY",
        "COVI": "Priority COVID Shipments Only",
    }

    _services_transit = {"GEN": 4, "PRI": 2, "BBE": 2, "BBEG": 4, "COVI": 2}

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._packages = self._ubbe_request["packages"]
        self._options = self._ubbe_request.get("carrier_options", [])
        self._is_test = DEBUG

        self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
            CALM_AIR
        ]["account"]
        self._carrier = self._ubbe_request["objects"]["carrier_accounts"][CALM_AIR][
            "carrier"
        ]
        self._login = self._carrier_account.username.decrypt()
        self._account_number = self._carrier_account.account_number.decrypt()
        # Rate Access Key
        self._password = self._carrier_account.password.decrypt()
        # Ship Access Key
        self._key = self._carrier_account.api_key.decrypt()
        # Track Access Key
        self._requestor = self._carrier_account.contract_number.decrypt()

        copied = copy.deepcopy(self._ubbe_request)

        if "dg_service" in copied:
            del copied["dg_service"]

        if "objects" in copied:
            del copied["objects"]

        self._error_world_request = copied

    def _build_packages(self) -> dict:
        """
        Build packages for calm air request.
        :return: package dictionary
        """

        total_quantity = 0
        total_weight = Decimal("0.0")
        total_count = 1
        description = ""

        params = {
            "dims_unit": "CM",
            "unit_of_weight": "KGS",
            "pieces": "0",
            "weight": "0",
            "goods": "",
        }

        for i, package in enumerate(self._packages):
            total_quantity += int(package["quantity"])
            total_weight += Decimal(
                Decimal(package["weight"]) * Decimal(package["quantity"])
            ).quantize(self._sig_fig)

            if i == 0:
                description = package["description"]
            else:
                description += f', {package["description"]}'

            params[f"dims{total_count}_pieces"] = package["quantity"]
            params[f"dims{total_count}_length"] = package["length"]
            params[f"dims{total_count}_width"] = package["width"]
            params[f"dims{total_count}_height"] = package["height"]

            total_count += 1

        if total_count != 5:
            # Add remaining empty packages
            for i in range(total_count, 6):
                params[f"dims{i}_pieces"] = self._zero
                params[f"dims{i}_length"] = self._zero
                params[f"dims{i}_width"] = self._zero
                params[f"dims{i}_height"] = self._zero

        params["pieces"] = total_quantity
        params["weight"] = total_weight
        params["goods"] = description[:20]

        return params
