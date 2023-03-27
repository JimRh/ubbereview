"""
    Title: Purolator Address Helper Unit Tests
    Description: Unit Tests for the Purolator Address Helpers. Test Everything.
    Created: November 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.test import TestCase

from api.apis.carriers.purolator.courier.helpers.packages import PurolatorPackages


class PurolatorPackagesTests(TestCase):
    def setUp(self):
        self.request_rate = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "packages": [
                {
                    "quantity": 1,
                    "length": "100",
                    "width": "50",
                    "height": "50",
                    "weight": "50",
                    "package_type": "BOX",
                }
            ],
        }

        self._puro_packages_rate = PurolatorPackages(
            ubbe_request=self.request_rate, is_rate=True
        )
        self._puro_packages_ship = PurolatorPackages(
            ubbe_request=self.request_rate, is_rate=False
        )

    def test_dim_field_length(self):
        package = self._puro_packages_rate._dim_field(
            dim=self.request_rate["packages"][0]["length"]
        )
        expected = {"Value": Decimal("100"), "DimensionUnit": "cm"}
        self.assertDictEqual(expected, package)

    def test_dim_field_width(self):
        package = self._puro_packages_rate._dim_field(
            dim=self.request_rate["packages"][0]["width"]
        )
        expected = {"Value": Decimal("50"), "DimensionUnit": "cm"}
        self.assertDictEqual(expected, package)

    def test_dim_field_height(self):
        package = self._puro_packages_rate._dim_field(
            dim=self.request_rate["packages"][0]["height"]
        )
        expected = {"Value": Decimal("50"), "DimensionUnit": "cm"}
        self.assertDictEqual(expected, package)

    def test_dim_field_weight(self):
        package = self._puro_packages_rate._dim_field(
            dim=self.request_rate["packages"][0]["weight"]
        )
        expected = {"Value": Decimal("50"), "DimensionUnit": "cm"}
        self.assertDictEqual(expected, package)

    def test_build_packages(self):
        package = self._puro_packages_rate._build_packages(service="Puro")
        expected = {
            "packages": [
                {
                    "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                    "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                    "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                    "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                    "Options": [],
                }
            ],
            "weight": Decimal("50"),
            "qty": Decimal("1"),
            "description": "Package",
        }

        self.assertDictEqual(expected, package)

    def test_packages(self):
        package = self._puro_packages_rate.packages()

        expected = {
            "ServiceID": "PurolatorExpress",
            "Description": "Package",
            "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
            "TotalPieces": Decimal("1"),
            "PiecesInformation": {
                "Piece": [
                    {
                        "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Options": [],
                    }
                ]
            },
        }

        self.assertDictEqual(expected, package)

    def test_packages_international(self):
        copied = copy.deepcopy(self.request_rate)
        copied["is_international"] = True

        packages_rate = PurolatorPackages(ubbe_request=copied, is_rate=True)

        package = packages_rate.packages()

        expected = {
            "ServiceID": "PurolatorExpressU.S.",
            "Description": "Package",
            "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
            "TotalPieces": Decimal("1"),
            "PiecesInformation": {
                "Piece": [
                    {
                        "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Options": [],
                    }
                ]
            },
        }

        self.assertDictEqual(expected, package)

    def test_packages_multiple(self):
        copied = copy.deepcopy(self.request_rate)
        copied["packages"].append(
            {
                "quantity": 2,
                "length": "80",
                "width": "30",
                "height": "30",
                "weight": "30",
                "package_type": "BOX",
            }
        )

        pack = PurolatorPackages(ubbe_request=copied, is_rate=False)
        package = pack.packages()

        expected = {
            "ServiceID": "PurolatorExpress",
            "Description": "Package Package",
            "TotalWeight": {"Value": Decimal("80"), "WeightUnit": "kg"},
            "TotalPieces": Decimal("3"),
            "PiecesInformation": {
                "Piece": [
                    {
                        "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Options": [],
                    },
                    {
                        "Weight": {"Value": Decimal("30"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("80"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Options": [],
                    },
                    {
                        "Weight": {"Value": Decimal("30"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("80"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Options": [],
                    },
                ]
            },
        }

        self.assertDictEqual(expected, package)

    def test_packages_service(self):
        package = self._puro_packages_rate.packages(service="PurolatorExpress9AM")

        expected = {
            "ServiceID": "PurolatorExpress9AM",
            "Description": "Package",
            "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
            "TotalPieces": Decimal("1"),
            "PiecesInformation": {
                "Piece": [
                    {
                        "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Options": [],
                    }
                ]
            },
        }

        self.assertDictEqual(expected, package)

    def test_packages_multiple_service(self):
        copied = copy.deepcopy(self.request_rate)
        copied["packages"].append(
            {
                "quantity": 2,
                "length": "80",
                "width": "30",
                "height": "30",
                "weight": "30",
                "package_type": "BOX",
            }
        )

        pack = PurolatorPackages(ubbe_request=copied, is_rate=False)
        package = pack.packages(service="PurolatorGround")

        expected = {
            "ServiceID": "PurolatorGround",
            "Description": "Package Package",
            "TotalWeight": {"Value": Decimal("80"), "WeightUnit": "kg"},
            "TotalPieces": Decimal("3"),
            "PiecesInformation": {
                "Piece": [
                    {
                        "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                        "Options": [],
                    },
                    {
                        "Weight": {"Value": Decimal("30"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("80"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Options": [],
                    },
                    {
                        "Weight": {"Value": Decimal("30"), "WeightUnit": "kg"},
                        "Length": {"Value": Decimal("80"), "DimensionUnit": "cm"},
                        "Width": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Height": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                        "Options": [],
                    },
                ]
            },
        }

        self.assertDictEqual(expected, package)
