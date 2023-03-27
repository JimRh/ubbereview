"""
    Title: Commodity Model
    Description: This file will contain functions for Commodity Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, PositiveIntegerField, DecimalField
from django.db.models.fields.related import ForeignKey

from api.globals.project import MAX_CHAR_LEN, MAX_WEIGHT_DIGITS, MAX_PRICE_DIGITS, COUNTRY_CODE_LEN, WEIGHT_PRECISION, \
    PRICE_PRECISION, BASE_TEN

from api.models.base_table import BaseTable


class Commodity(BaseTable):
    """
        Commodity Model
    """
    _weight_sig_fig = Decimal(str(BASE_TEN ** (WEIGHT_PRECISION * -1)))
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))

    shipment = ForeignKey("Shipment", on_delete=CASCADE, related_name="commodity_shipment")
    description = CharField(max_length=MAX_CHAR_LEN)
    quantity = PositiveIntegerField()
    total_weight = DecimalField(max_digits=MAX_WEIGHT_DIGITS, decimal_places=WEIGHT_PRECISION)
    unit_value = DecimalField(max_digits=MAX_PRICE_DIGITS, decimal_places=PRICE_PRECISION)
    country_code = CharField(max_length=COUNTRY_CODE_LEN)
    package = PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Commodity"
        verbose_name_plural = "Shipment - Commodities"

    # TODO: Bulk save Change to save to package?
    @staticmethod
    def one_step_save(shipment, commodities_json: list) -> None:
        """
            Save commodities to shipment
            :param shipment: Shipment
            :param commodities_json: commodity list of dicts
            :return: None
        """

        for i, commodity in enumerate(commodities_json):
            new_commodity = Commodity()
            new_commodity.description = commodity["description"]
            new_commodity.quantity = commodity.get("quantity", 1)
            new_commodity.total_weight = Decimal(commodity["total_weight"])
            new_commodity.unit_value = Decimal(commodity["unit_value"])
            new_commodity.country_code = commodity["made_in_country_code"]
            new_commodity.package = commodity.get("package", i + 1)
            new_commodity.shipment = shipment

            new_commodity.save()

    def next_leg_json(self) -> dict:
        """
            Get Next Leg commodity dict
            :return: Commodity dict
        """
        return {
            "description": self.description,
            "made_in_country_code": self.country_code,
            "package": self.package,
            "quantity": self.quantity,
            "quantity_unit_of_measure": "Each",
            "total_weight": self.total_weight,
            "unit_value": self.unit_value
        }

    # Override
    def save(self, *args, **kwargs):
        self.total_weight = self.total_weight.quantize(self._weight_sig_fig)
        self.unit_value = self.unit_value.quantize(self._price_sig_fig)
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Commodity ({self.description}: {self.country_code}, {self.description}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.description}: {self.country_code}, {self.description}"
