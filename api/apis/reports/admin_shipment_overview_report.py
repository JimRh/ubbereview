"""
    Title: Admin Shipment Overview Report Data
    Description: The class filter requested filters and return the following:
        - Start Date
        - End Date
    Created: August 10, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from decimal import Decimal
from django.db.models import QuerySet
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from pytz import timezone

from api.apis.reports.report_types.excel_report import ExcelReport
from api.models import Shipment


class AdminShipmentOverviewReport:
    """
        Shipment Metric Api
    """
    _zero = Decimal("0.00")

    headings = [
        "ID",
        "Central File",
        "Date",
        "BC Code",
        "BC Name",
        "Account",
        "Username",
        "Starting Origin Company",
        "Starting Origin Name",
        "Starting Origin City",
        "Starting Origin Postal",
        "Starting Origin Province",
        "Final Destination Company",
        "Final Destination Name",
        "Final Destination City",
        "Final Destination Postal",
        "Final Destination Province",
        "Reference One",
        "Reference Two",
        "Project",
        "Package QTY Total",
        "Weight Total - KG",
        "Insurance Amount",
        "Insurance Cost",
        "BBE - Freight",
        "BBE - Surcharges",
        "BBE - Taxes",
        "BBE - Total Cost w/Tax",
        "BBE - Total Cost (No Tax)",
        "Marked up - Freight",
        "Marked up - Surcharges",
        "Marked up - Taxes",
        "Marked up - Price w/Tax",
        "Marked up - Price (No Tax)",
        "P: ID",
        "P: Carrier",
        "P: Carrier Service",
        "P: Carrier Tracking Number",
        "P: Carrier Pickup Number",
        "P: Origin City",
        "P: Origin Postal",
        "P: Origin Province",
        "P: Destination City",
        "P: Destination Postal",
        "P: Destination Province",
        "P: Est. Delivery Date",
        "P: Delivered Date",
        "P: BBE -Freight",
        "P: BBE -Surcharges",
        "P: BBE -Taxes",
        "P: BBE - Cost w/Tax",
        "P: BBE - Cost (No Tax)",
        "P: Carrier Markup (%)",
        "P: Marked up - Freight",
        "P: Marked up - Surcharges",
        "P: Marked up - Taxes",
        "P: Marked up - Price w/Tax",
        "P: Marked up - (No Tax)",
        "M: ID",
        "M: Carrier",
        "M: Carrier Service",
        "M: Carrier Tracking Number",
        "M: Carrier Pickup Number",
        "M: Origin City",
        "M: Origin Postal",
        "M: Origin Province",
        "M: Destination City",
        "M: Destination Postal",
        "M: Destination Province",
        "M: Est. Delivery Date",
        "M: Delivered Date",
        "M: BBE -Freight",
        "M: BBE -Surcharges",
        "M: BBE -Taxes",
        "M: BBE - Cost w/Tax",
        "M: BBE - Cost (No Tax)",
        "M: Carrier Markup (%)",
        "M: Marked up - Freight",
        "M: Marked up - Surcharges",
        "M: Marked up - Taxes",
        "M: Marked up - Price w/Tax",
        "M: Marked up - (No Tax)",
        "D: ID",
        "D: Carrier",
        "D: Carrier Service",
        "D: Carrier Tracking Number",
        "D: Carrier Pickup Number",
        "D: Origin City",
        "D: Origin Postal",
        "D: Origin Province",
        "D: Destination City",
        "D: Destination Postal",
        "D: Destination Province",
        "D: Est. Delivery Date",
        "D: Delivered Date",
        "D: BBE -Freight",
        "D: BBE -Surcharges",
        "D: BBE -Taxes",
        "D: BBE - Cost w/Tax",
        "D: BBE - Cost (No Tax)",
        "D: Carrier Markup (%)",
        "D: Marked up - Freight",
        "D: Marked up - Surcharges",
        "D: Marked up - Taxes",
        "D: Marked up - Price w/Tax",
        "D: Marked up - (No Tax)",
    ]

    def __init__(self):
        pass

    @staticmethod
    def _create_shipment_data(shipment: Shipment) -> list:
        creation_date = shipment.creation_date.strftime("%Y-%m-%d")

        leg_list = []
        legs = shipment.leg_shipment.all()

        if len(legs) == 1:
            leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
        elif len(legs) > 1:
            first_leg = legs.first()

            if first_leg.type == "M":
                leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])

        pre_markup_freight = Decimal("0.00")
        pre_markup_surcharge = Decimal("0.00")
        pre_markup_tax = Decimal("0.00")
        pre_markup_cost = Decimal("0.00")
        pre_markup_pre_tax = Decimal("0.00")

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

            pre_markup_freight += leg.freight
            pre_markup_surcharge += leg.surcharge
            pre_markup_tax += leg.tax
            pre_markup_cost += leg.cost
            pre_markup_pre_tax += leg.cost - leg.tax

            freight += leg_freight
            surcharge += leg_surcharge
            tax += leg_tax
            cost += leg_cost
            pre_tax += leg_pre_tax

            est_date = leg.estimated_delivery_date.strftime("%Y-%m-%d")
            delivered_date = leg.delivered_date.strftime("%Y-%m-%d")

            if est_date == "1-01-01":
                est_date = ""

            if delivered_date == "1-01-01":
                delivered_date = ""

            leg_list.append([
                leg.leg_id,
                leg.carrier.name,
                leg.service_name,
                leg.tracking_identifier,
                leg.carrier_pickup_identifier,
                leg.origin.city,
                leg.origin.postal_code,
                leg.origin.province.code,
                leg.destination.city,
                leg.destination.postal_code,
                leg.destination.province.code,
                est_date,
                delivered_date,
                leg.freight,
                leg.surcharge,
                leg.tax,
                leg.cost,
                (leg.cost - leg_tax).quantize(Decimal("0.01")),
                leg.markup,
                leg_freight.quantize(Decimal("0.01")),
                leg_surcharge.quantize(Decimal("0.01")),
                leg_tax.quantize(Decimal("0.01")),
                leg_cost.quantize(Decimal("0.01")),
                leg_pre_tax.quantize(Decimal("0.01")),
            ])

        package_data = shipment.package_shipment.all().aggregate(
            total_packages=Sum('quantity'),
            total_weight=Sum(F('quantity') * F('weight'))
        )

        total_qty = package_data["total_packages"] if package_data.get("total_packages") else Decimal("0")
        total_weight = package_data["total_weight"] if package_data.get("total_weight") else Decimal("0")

        ret = [
            shipment.shipment_id,
            shipment.ff_number,
            creation_date,
            shipment.bc_customer_code,
            shipment.bc_customer_name,
            shipment.subaccount.contact.company_name,
            shipment.username,
            shipment.sender.company_name,
            shipment.sender.name,
            shipment.origin.city,
            shipment.origin.postal_code,
            shipment.origin.province.code,
            shipment.receiver.company_name,
            shipment.receiver.name,
            shipment.destination.city,
            shipment.destination.postal_code,
            shipment.destination.province.code,
            shipment.reference_one,
            shipment.reference_two,
            shipment.project,
            Decimal(total_qty).quantize(Decimal("0.01")),
            Decimal(total_weight).quantize(Decimal("0.01")),
            shipment.insurance_amount,
            shipment.insurance_cost,
            pre_markup_freight.quantize(Decimal("0.01")),
            pre_markup_surcharge.quantize(Decimal("0.01")),
            pre_markup_tax.quantize(Decimal("0.01")),
            pre_markup_cost.quantize(Decimal("0.01")),
            pre_markup_pre_tax.quantize(Decimal("0.01")),
            freight.quantize(Decimal("0.01")),
            surcharge.quantize(Decimal("0.01")),
            tax.quantize(Decimal("0.01")),
            cost.quantize(Decimal("0.01")),
            pre_tax.quantize(Decimal("0.01"))
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
