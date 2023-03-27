"""
    Title: Purolator Packages
    Description: This file will contain helper functions related to Purolator packages specs.
    Created: November 19, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal


class PurolatorPackages:
    """
    Purolator Packages
    """

    def __init__(self, ubbe_request: dict, is_rate: bool) -> None:
        self._ubbe_request = ubbe_request
        self._is_rate = is_rate
        self._options = []

    @staticmethod
    def _dim_field(dim: Decimal) -> dict:
        """
        Format dim field into puro weight object.
        :param dim:
        :return:
        """
        return {"Value": Decimal(dim), "DimensionUnit": "cm"}

    def _build_dg_options(self, package: dict, service: str):
        """

        :param package:
        :param service:
        :return:
        """

        if "Express" not in service:
            mode = "Ground"
        else:
            mode = "Air"

        if package["un_number"] == 3373:
            un = "UN3373"
        elif package["un_number"] == 1845:
            un = "UN1845"
        else:
            un = "FullyRegulated"

        self._options.append(
            {
                "OptionIDValuePair": [
                    {
                        "ID": "DangerousGoods",
                        "Value": True,
                    },
                    {
                        "ID": "DangerousGoodsClass",
                        "Value": un,
                    },
                    {"ID": "DangerousGoodsMode", "Value": mode},
                ]
            }
        )

    def _build_packages(self, service: str) -> dict:
        """
        Create puro package list object.
        :return:
        """
        total_qty = Decimal("0.00")
        total_weight = Decimal("0.00")
        description = []
        puro_packages = []

        for package in self._ubbe_request["packages"]:
            description.append(package.get("description", "Package"))
            total_qty += Decimal(package["quantity"])
            total_weight += Decimal(package["weight"])

            for i in range(0, package["quantity"]):
                puro_packages.append(
                    {
                        "Weight": {
                            "Value": Decimal(package["weight"]),
                            "WeightUnit": "kg",
                        },
                        "Length": self._dim_field(dim=package["length"]),
                        "Width": self._dim_field(dim=package["width"]),
                        "Height": self._dim_field(dim=package["height"]),
                        "Options": [],
                    }
                )

            if self._ubbe_request.get("is_dangerous_goods", False) and package.get(
                "un_number"
            ):
                self._build_dg_options(package=package, service=service)

        return {
            "packages": puro_packages,
            "weight": total_weight.quantize(Decimal("1")),
            "qty": total_qty.quantize(Decimal("1")),
            "description": " ".join(description),
        }

    def packages(self, service: str = "") -> dict:
        """
        Create puro package soap object.
        :return:
        """

        if not service:
            if self._ubbe_request.get("is_international", False):
                o_country = self._ubbe_request["origin"]["country"]
                d_country = self._ubbe_request["destination"]["country"]

                if o_country not in ["US", "CA"] or d_country not in ["US", "CA"]:
                    service = "PurolatorExpressInternational"
                else:
                    service = "PurolatorExpressU.S."

            else:
                service = "PurolatorExpress"

        packages = self._build_packages(service=service)

        ret = {
            "ServiceID": service,
            "Description": str(packages["description"])[:25],
            "TotalWeight": {"Value": packages["weight"], "WeightUnit": "kg"},
            "TotalPieces": packages["qty"],
            "PiecesInformation": {"Piece": packages["packages"]},
        }

        # TODO - FINISH Options

        if self._ubbe_request.get("is_dangerous_goods", False):
            ret.update(
                {
                    "DangerousGoodsDeclarationDocumentIndicator": False,
                    "OptionsInformation": {"Options": self._options},
                }
            )

        return ret
