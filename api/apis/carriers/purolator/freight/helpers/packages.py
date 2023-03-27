"""
    Title: Purolator Freight Packages
    Description: This file will contain helper functions related to Purolator Freight packages specs.
    Created: December 15, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal


class PurolatorFreightPackages:
    """
    Purolator Freight Packages
    """

    def __init__(self, is_rate: bool) -> None:
        self._is_rate = is_rate

    @staticmethod
    def _dim_field(dim: Decimal) -> dict:
        """
        Format dim field into puro weight object.
        :param dim:
        :return:
        """
        return {"Value": Decimal(dim), "DimensionUnit": "cm"}

    def _build_packages(self, packages: list) -> list:
        """
        Create puro package list object.
        :param packages: package list in ubbe request.
        :return:
        """
        count = 1
        puro_packages = []

        for package in packages:
            puro_packages.append(
                {
                    "LineItem": {
                        "LineNumber": count,
                        "Pieces": package["quantity"],
                        "HandlingUnit": package["quantity"],
                        "HandlingUnitType": package["package_type"],
                        "Description": package.get("description", "Package"),
                        "Weight": {
                            "Value": Decimal(package["weight"]),
                            "WeightUnit": "kg",
                        },
                        "FreightClass": "",
                        "Length": self._dim_field(dim=package["length"]),
                        "Width": self._dim_field(dim=package["width"]),
                        "Height": self._dim_field(dim=package["height"]),
                    }
                }
            )
            count += 1

        return puro_packages

    def packages(self, packages: list) -> list:
        """
        Create puro package soap object.
        :return:
        """

        return self._build_packages(packages=packages)
