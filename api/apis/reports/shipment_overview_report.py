"""
    Title: Shipment Overview Report Data
    Description: The class filter requested filters and return thee following:
        - Start Date
        - End Date
    Created: June 16, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal
from django.db.models import QuerySet
from django.db.models.aggregates import Sum
from django.db.models.expressions import F

from api.apis.reports.report_types.excel_report import ExcelReport
from api.models import Shipment


class ShipmentOverviewReportData:
    """
        Shipment Metric Api
    """
    _zero = Decimal("0.00")

    headings = [
        "ID",
        "Date",
        "Username",
        "Starting Company",
        "Starting Name",
        "Starting Address",
        "Starting Origin City",
        "Starting Origin Postal",
        "Starting Origin Province",
        "Final Destination City",
        "Final Destination Postal",
        "Final Destination Province",
        "Reference One",
        "Reference Two",
        "Package QTY Total",
        "Weight Total - KG",
        "Insurance Amount",
        "Insurance Cost",
        "Freight",
        "Surcharge",
        "Taxes",
        "Price w/Tax",
        "Price No Tax",
        "P: ID",
        "P: Carrier",
        "P: Carrier Reference",
        "P: Origin City",
        "P: Origin Postal",
        "P: Origin Province",
        "P: Destination City",
        "P: Destination Postal",
        "P: Destination Province",
        "P: Freight",
        "P: Surcharge",
        "P: Taxes",
        "P: Price w/Tax",
        "P: Price No Tax",
        "M: ID",
        "M: Carrier",
        "M: Carrier Reference",
        "M: Origin City",
        "M: Origin Postal",
        "M: Origin Province",
        "M: Destination City",
        "M: Destination Postal",
        "M: Destination Province",
        "M: Freight",
        "M: Surcharge",
        "M: Taxes",
        "M: Price w/Tax",
        "M: Price No Tax",
        "D: ID",
        "D: Carrier",
        "D: Carrier Reference",
        "D: Origin City",
        "D: Origin Postal",
        "D: Origin Province",
        "D: Destination City",
        "D: Destination Postal",
        "D: Destination Province",
        "D: Freight",
        "D: Surcharge",
        "D: Taxes",
        "D: Price w/Tax",
        "D: Price No Tax",
    ]

    def __init__(self, is_price_hide: bool = False):
        self.is_price_hide = is_price_hide

    def _create_shipment_data(self, shipment: Shipment) -> list:
        creation_date = shipment.creation_date.strftime("%Y-%m-%d")

        leg_list = []
        legs = shipment.leg_shipment.all()

        if len(legs) == 1:
            leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])
        elif len(legs) > 1:
            first_leg = legs.first()

            if first_leg.type == "M":
                leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])

        freight = Decimal("0.00")
        surcharge = Decimal("0.00")
        tax = Decimal("0.00")
        cost = Decimal("0.00")
        pre_tax = Decimal("0.00")

        for leg in legs:
            markup_multiplier = (leg.markup / 100 + 1)

            leg_freight = leg.freight * markup_multiplier
            leg_surcharge = leg.surcharge * markup_multiplier
            leg_tax = leg.tax * markup_multiplier
            leg_cost = leg.cost * markup_multiplier
            leg_pre_tax = leg_cost - leg_tax

            freight += leg_freight
            surcharge += leg_surcharge
            tax += leg_tax
            cost += leg_cost
            pre_tax += leg_pre_tax

            leg_list.append([
                leg.leg_id,
                leg.carrier.name,
                leg.tracking_identifier,
                leg.origin.city,
                leg.origin.postal_code,
                leg.origin.province.code,
                leg.destination.city,
                leg.destination.postal_code,
                leg.destination.province.code,
                "-" if self.is_price_hide else leg_freight.quantize(Decimal("0.01")),
                "-" if self.is_price_hide else leg_surcharge.quantize(Decimal("0.01")),
                "-" if self.is_price_hide else leg_tax.quantize(Decimal("0.01")),
                "-" if self.is_price_hide else leg_cost.quantize(Decimal("0.01")),
                "-" if self.is_price_hide else leg_pre_tax.quantize(Decimal("0.01"))
            ])

        package_data = shipment.package_shipment.all().aggregate(
            total_packages=Sum('quantity'),
            total_weight=Sum(F('quantity') * F('weight'))
        )

        total_qty = package_data["total_packages"] if package_data.get("total_packages") else Decimal("0")
        total_weight = package_data["total_weight"] if package_data.get("total_weight") else Decimal("0")

        ret = [
            shipment.shipment_id,
            creation_date,
            shipment.username,
            shipment.sender.company_name,
            shipment.sender.name,
            shipment.origin.address,
            shipment.origin.city,
            shipment.origin.postal_code,
            shipment.origin.province.code,
            shipment.destination.city,
            shipment.destination.postal_code,
            shipment.destination.province.code,
            shipment.reference_one,
            shipment.reference_two,
            Decimal(total_qty).quantize(Decimal("0.01")),
            Decimal(total_weight).quantize(Decimal("0.01")),
            shipment.insurance_amount,
            shipment.insurance_cost,
            "-" if self.is_price_hide else freight.quantize(Decimal("0.01")),
            "-" if self.is_price_hide else surcharge.quantize(Decimal("0.01")),
            "-" if self.is_price_hide else tax.quantize(Decimal("0.01")),
            "-" if self.is_price_hide else cost.quantize(Decimal("0.01")),
            "-" if self.is_price_hide else pre_tax.quantize(Decimal("0.01"))
        ]
        for l_list in leg_list:
            ret += l_list

        return ret

    def _get_shipment_overview_data(self, shipments) -> list:
        ret = []

        for shipment in shipments:
            ret.append(self._create_shipment_data(shipment=shipment))

        return ret

    def get_shipment_overview(self, shipments: QuerySet, file_name: str) -> dict:
        """
                  Get Shipment Overview Report for all modes of transportation data.
                  :return: list of shipment overview data.
              """

        shipment_overview_data = self._get_shipment_overview_data(shipments=shipments)

        sheet = ExcelReport(headings=self.headings, data=shipment_overview_data).create_report()

        return {
            "type": "excel",
            "file": sheet,
            "filename": file_name
        }