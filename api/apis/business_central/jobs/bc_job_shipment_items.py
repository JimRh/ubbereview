"""
    Title: Business Central Shipment Items
    Description: This file will contain all functions to create Business Central Shipment Items.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from decimal import Decimal

from django.db import connection

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase
from api.background_tasks.logger import CeleryLogger
from api.general.convert import Convert


class BCJobShipmentItems(BCJobBase):
    """
            Create Shipment Items
    """

    _summary_line = 1
    _detail_line = 2
    _dim_unit = 4
    _item = 2

    def __init__(self, ubbe_data: dict, shipment):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)
        self._request_list = []
        self._total_description = ""
        self._total_qty = Decimal("0")
        self._total_weight_kg = Decimal("0")
        self._total_weight_lbs = Decimal("0")
        self._total_cubage = Decimal("0")
        self._total_cubic_inches = Decimal("0")
        self._total_cubic_feet = Decimal("0")
        self._total_cubic_meter = Decimal("0")
        self._total_square_meter = Decimal("0")
        self._total_square_feet = Decimal("0")
        self._total_rev_ton = Decimal("0")
        self._total_dim_rev_ton = Decimal("0")
        self._length = Decimal("0")
        self._width = Decimal("0")
        self._height = Decimal("0")

    def _create_package(self, package):
        """
            Create request for shipment item/
            :return: Package Dict
        """

        description = package.description
        qty = Decimal(package.quantity)
        kg_weight = package.weight
        cm_length = package.length
        cm_width = package.width
        cm_height = package.height

        lbs_weight = Convert().kgs_to_lbs(weight=kg_weight)
        cubage = Convert().cubage_cm(qty=qty, length=cm_length, width=cm_width, height=cm_height)

        in_length = Convert().cms_to_inches(length=cm_length)
        in_width = Convert().cms_to_inches(length=cm_width)
        in_height = Convert().cms_to_inches(length=cm_height)
        cubic_inches = Convert().cubic_in(qty=qty, length=in_length, width=in_width, height=in_height)
        cubic_feet = Convert().cubic_in_to_cubic_feet(value=cubic_inches)
        cubic_meter = Convert().cubic_in_to_cubic_feet(value=cubic_inches)
        square_meter = Convert().cms_to_square_meters(length=cm_length, width=cm_width)
        square_feet = Convert().square_meters_to_square_feet(value=square_meter)
        rev_ton = Convert().kg_to_rev_ton(weight=kg_weight)
        dim_rev_ton = Convert().dim_rev_ton(qty=qty, length=in_length, width=in_width, height=in_height)

        if len(package.description) >= 50:
            description = package.description[:47] + "..."

        if package.package_type in ["DG", "PHFRO", "PHREF", "PHCONR", "PHEXR"]:
            p_type = "BOX"
        else:
            p_type = package.package_type

        request = {
            "FunctionName": "AddShipmentItems",
            "JobNo": self._job_number,
            "ShipmentItemID": package.package_id,
            "LineType": self._detail_line,
            "Type": self._item,
            "CustomerReference": package.package_account_id,
            "Description": description,
            "ActualQuantity": qty,
            "ActualQuantityUOM": p_type,
            "ActualWeightKG": kg_weight,
            "ActualDimsUOM": self._dim_unit,
            "ActualLength": cm_length,
            "ActualWidth": cm_width,
            "ActualHeight": cm_height,
            "ActualCubage": cubage,
            "ActualRevenueTons": dim_rev_ton,
            "CubicInches": cubic_inches,
            "CubicFeet": cubic_feet,
            "CubicMeters": cubic_meter,
            "SquareFeet": square_feet,
            "SquareMeters": square_meter
        }

        # Add DG fields if shipment is DG
        if package.un_number != 0:
            dg_description = package.dg_proper_name

            if len(package.dg_proper_name) >= 50:
                dg_description = package.dg_proper_name[:47] + "..."

            request.update({
                "DangerousGoodsProperName": dg_description,
                "DangerousGoodsQuantity": package.dg_quantity,
                "DangerousGoodsClass": package.un_number,
                "DangerousGoodsProperUN": package.un_number,
                "DangerousGoodsProperPackingGroup": package.packing_group.description,
                "DangerousGoodsProperWeightKG": kg_weight,
            })

        # Update summary line information
        self._length += cm_length

        if self._width < cm_width:
            self._width = cm_width

        if self._height < cm_height:
            self._height = cm_height

        self._total_description += description + ", "
        self._total_qty += qty
        self._total_weight_kg += kg_weight
        self._total_weight_lbs += lbs_weight
        self._total_cubage += cubage
        self._total_cubic_inches += cubic_inches
        self._total_cubic_feet += cubic_feet
        self._total_cubic_meter += cubic_meter
        self._total_square_meter += square_meter
        self._total_square_feet += square_feet
        self._total_rev_ton += rev_ton
        self._total_dim_rev_ton += dim_rev_ton

        return request

    def _build_shipment_items(self) -> None:
        """
            Create shipment_items request
        """
        packages = self._shipment.package_shipment.all()

        for package in packages:
            # Create Package for request
            self._request_list.append(self._create_package(package=package))

        if len(self._total_description) >= 50:
            description = self._total_description[:47] + "..."
        else:
            description = self._total_description

        if packages[0].package_type == "DG":
            p_type = "BOX"
        else:
            p_type = packages[0].package_type

        self._summary_package = {
            "FunctionName": "AddShipmentItems",
            "JobNo": self._job_number,
            "ShipmentItemID": self._shipment.shipment_id,
            "LineType": self._summary_line,
            "Type": self._item,
            "CustomerReference": self._shipment.account_id,
            "Description": description,
            "ActualQuantity": self._total_qty,
            "ActualQuantityUOM": p_type,
            "ActualWeightKG": self._total_weight_kg,
            "ActualDimsUOM": self._dim_unit,
            "ActualLength": self._length,
            "ActualWidth": self._width,
            "ActualHeight": self._height,
            "ActualCubage": self._total_cubage,
            "ActualRevenueTons": self._total_dim_rev_ton,
            "CubicInches": self._total_cubic_inches,
            "CubicFeet": self._total_cubic_feet,
            "CubicMeters": self._total_cubic_meter,
            "SquareFeet": self._total_square_feet,
            "SquareMeters": self._total_square_meter
        }

    def _send_items(self):
        response_list = []

        # Post Data to Summary Package to Business Central
        try:
            response = self._post(request=self._summary_package)
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(message="Failed to send shipment items", data=self._summary_package)

        for package in self._request_list:

            # Post Data to Detail Package to Business Central
            try:
                response = self._post(request=package)
            except BusinessCentralError as e:
                connection.close()
                raise BusinessCentralError(message=f"Failed to send shipment items: {str(e.message)}", data=package)

            response_list.append({"package_id": package["ShipmentItemID"], "bc_id": response})

        return response_list

    def create_shipment_items(self) -> list:
        """
            Create add shipment items to an existing job File.
            :return: Dictionary with FF File number
        """

        if not self._job_number:
            raise BusinessCentralError(message="Job Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            self._build_shipment_items()
        except(BusinessCentralError, KeyError) as e:
            connection.close()
            CeleryLogger().l_debug.delay(location="bc_job_shipment_items.py line: 180", message=str(e.message))
            raise BusinessCentralError(message=f"{self._job_number}: Failed to build request", data=str(e.message))

        # Post Data to Business Central
        try:
            response = self._send_items()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_debug.delay(location="bc_job_shipment_items.py line: 187", message=str(e.message))
            raise BusinessCentralError(message=f"{self._job_number}: Shipment Items Failed", data=str(e.message))

        return response

    def create_account_shipment_items(self) -> list:
        """
            Create add shipment items to an existing Freight Forwarding File.
            :return: Dictionary with FF File number
        """

        if not self._job_number:
            raise BusinessCentralError(message="FF Number empty", data=self._job_number)

        # Build request data to Business Central
        self._request_list = [
            {
                "FunctionName": "AddShipmentItems",
                "FFFileNo": self._job_number,
                "ShipmentItemID": self._shipment.shipment_id,
                "LineType": self._summary_line,
            },
            {
                "FunctionName": "AddShipmentItems",
                "FFFileNo": self._job_number,
                "ShipmentItemID": self._shipment.shipment_id + "-1",
                "LineType": self._detail_line,
            }
        ]

        # Post Data to Business Central
        try:
            response = self._send_items()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_debug.delay(location="shipment_items.py line: 187", message=str(e.message))
            raise BusinessCentralError(message=f"{self._job_number}: Shipment Items Failed", data=str(e.message))

        return response

