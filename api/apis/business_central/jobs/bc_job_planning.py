"""
    Title: Business Central Job Planning Lines
    Description: This file will contain all functions to create Business Central Job Planning Lines.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase
from api.background_tasks.logger import CeleryLogger
from api.models import BBECityAlias


class BCJobPlanningLines(BCJobBase):
    """
            Create Job Planning Lines

            Budget Line = Expense

            Billable Line = Revenue

            Budget and Billable = Cost Plus

    """

    def __init__(self, ubbe_data: dict, shipment):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)

        self._planning_lines = ubbe_data.get("bc_planning_lines", [])
        self._request_list = []

    _item = 2
    _billable = 2
    _budget = 1

    def _build_requests(self):
        """
            Build Request for each planning line.
            :return:
        """

        for bc_leg in self._planning_lines:

            if bc_leg["leg"] in ["Handling"]:
                self._request_list.append(self._build_other(bc_leg=bc_leg))
                continue
            elif bc_leg["leg"] == "Allin":
                self._request_list.append(self._build_all_inclusive(bc_leg=bc_leg))
                continue

            try:
                from api.models import Leg
                leg = Leg.objects.get(
                    shipment=self._shipment, carrier__code=int(bc_leg["carrier_id"]), type=bc_leg["leg"]
                )
            except ObjectDoesNotExist:
                raise BusinessCentralError(message="Leg could not be found.", data=bc_leg["carrier_id"])

            if leg.service_code == "PICK_DEL" or leg.service_code == "BBEQUO":
                continue

            request = self._build(leg=leg, bc_leg=bc_leg)

            self._request_list.append(request)

    def _build(self, leg, bc_leg: dict) -> dict:
        """
            Create Job Planning Lines for each ubbe leg.
            :param leg: ubbe leg object
            :param bc_leg: Planning Line data
            :return: dictionary formatted to Job Planning Line
        """
        leg_id = leg.leg_id
        sub_total = leg.cost - leg.tax
        o_province = leg.origin.province
        d_province = leg.destination.province

        origin_city = BBECityAlias.check_alias(
            alias=leg.origin.city, province_code=o_province.code, country_code=o_province.country.code
        )

        destination_city = BBECityAlias.check_alias(
            alias=leg.destination.city, province_code=d_province.code, country_code=d_province.country.code
        )

        ret = {
            "FunctionName": "AddJobPlanningLine",
            "JobNo": self._job_number,
            "LineType": int(bc_leg["line_type"]),
            "LegID": leg_id,
            "LineID": f"{leg_id}-P",
            "Description": f"{leg_id}: {leg.carrier.get_mode_display()} - {origin_city} to {destination_city}"[:50],
            "Type": self._item,
            "No": bc_leg["item"],
            "ExpectedVendorNo": leg.carrier.bc_vendor_code,
            "VendorReferenceNo": leg.tracking_identifier if leg.tracking_identifier else self._shipment.shipment_id,
            "ExpectedCost": sub_total,
        }

        if bc_leg.get("branch_code") and bc_leg.get("cost_centre") and bc_leg.get("location_code"):
            ret["BranchCode"] = bc_leg["branch_code"]
            ret["CostCenterCode"] = bc_leg["cost_centre"]
            ret["LocationCode"] = bc_leg["location_code"]
        else:
            ret["UserID"] = self._bc_username

        if "markup" in bc_leg and bc_leg.get("markup", "") != "":
            ret["ExpectedRevenue"] = (leg.cost - leg.tax) * (self._one + (Decimal(str(bc_leg["markup"])) / self._hundred))
            ret["MarkupPercentage"] = bc_leg["markup"]

        if leg.markup > Decimal("0.00"):
            revenue_amount = sub_total * (self._one + (leg.markup / self._hundred))
            ret["ExpectedRevenue"] = Decimal(revenue_amount).quantize(Decimal("0.01"))
            ret["MarkupPercentage"] = leg.markup

        return ret

    def _build_other(self, bc_leg: dict) -> dict:
        """
            Build Business Central Planning Line requests other then legs
            :param bc_leg: Planning Line data
            :return: dictionary formatted to Job Planning Line
        """

        ret = {
            "FunctionName": "AddJobPlanningLine",
            "JobNo": self._job_number,
            "LineType": bc_leg["line_type"],
            "LegID": f"{self._shipment.shipment_id}M",
            "LineID": f"{self._shipment.shipment_id}-{bc_leg['leg'][:2]}",
            "Description": f'{bc_leg["leg"]}',
            "Type": self._item,
            "No": bc_leg["item"],
        }

        if bc_leg.get("branch_code") and bc_leg.get("cost_centre") and bc_leg.get("location_code"):
            ret["BranchCode"] = bc_leg["branch_code"]
            ret["CostCenterCode"] = bc_leg["cost_centre"]
            ret["LocationCode"] = bc_leg["location_code"]
        else:
            ret["UserID"] = self._bc_username

        return ret

    def _build_all_inclusive(self, bc_leg: dict) -> dict:
        """
            Build Business Central Planning Line requests other then legs
            :param bc_leg: Planning Line data
            :return: dictionary formatted to Job Planning Line
        """
        cost_amount = Decimal("0.00")

        for leg in self._shipment.leg_shipment.all():
            cost_amount += leg.cost - leg.tax

        ret = {
            "FunctionName": "AddJobPlanningLine",
            "JobNo": self._job_number,
            "LineType": bc_leg["line_type"],
            "LegID": f"{self._shipment.shipment_id}M",
            "LineID": f"{self._shipment.shipment_id}-{bc_leg['leg'][:2]}",
            "Description": f'All Inclusive',
            "Type": self._item,
            "No": bc_leg["item"],
            "ExpectedCost": cost_amount,
            "ExpectedRevenue": cost_amount,
        }

        if bc_leg.get("branch_code") and bc_leg.get("cost_centre") and bc_leg.get("location_code"):
            ret["BranchCode"] = bc_leg["branch_code"]
            ret["CostCenterCode"] = bc_leg["cost_centre"]
            ret["LocationCode"] = bc_leg["location_code"]
        else:
            ret["UserID"] = self._bc_username

        if "markup" in bc_leg and bc_leg.get("markup", "") != "":
            ret["ExpectedRevenue"] = cost_amount * (self._one + (Decimal(str(bc_leg["markup"])) / self._hundred))
            ret["MarkupPercentage"] = bc_leg["markup"]

        return ret

    def _build_insurance(self, is_account: bool) -> None:
        """
            Build Business Central Planning Line requests other then legs
            :param bc_leg: Planning Line data
            :return: dictionary formatted to Job Planning Line
        """
        description = f'Insurance valued at {self._shipment.insurance_amount}'

        billable = {
            "FunctionName": "AddJobPlanningLine",
            "JobNo": self._job_number,
            "LineType": self._billable,
            "LegID": f"{self._shipment.shipment_id}M",
            "LineID": f"{self._shipment.shipment_id}MI",
            "Description": description,
            "Type": self._item,
            "No": "INSURANCE",
            "ExpectedRevenue": self._shipment.insurance_cost,
            "VendorReferenceNo": "AON"
        }

        budget = {
            "FunctionName": "AddJobPlanningLine",
            "JobNo": self._job_number,
            "LineType": self._budget,
            "LegID": f"{self._shipment.shipment_id}M",
            "LineID": f"{self._shipment.shipment_id}MIB",
            "Description": description,
            "Type": self._item,
            "No": "INSURANCE",
            "ExpectedCost": Decimal("0.01"),
            "VendorReferenceNo": "AON"
        }

        if is_account:
            billable["LocationCode"] = self._shipment.subaccount.bc_location_code
            budget["LocationCode"] = self._shipment.subaccount.bc_location_code
        else:
            billable["LocationCode"] = self._bc_location
            billable["UserID"] = self._bc_username

            budget["LocationCode"] = self._bc_location
            budget["UserID"] = self._bc_username

        self._request_list.append(budget)
        self._request_list.append(billable)

    def _build_promo(self, is_account: bool) -> None:
        """
            Build Business Central Planning Line requests other then legs
            :param bc_leg: Planning Line data
            :return: dictionary formatted to Job Planning Line
        """

        billable = {
            "FunctionName": "AddJobPlanningLine",
            "JobNo": self._job_number,
            "LineType": self._billable,
            "LegID": f"{self._shipment.shipment_id}M",
            "LineID": f"{self._shipment.shipment_id}MP",
            "Description": f"Promo: {self._shipment.promo_code} - {self._shipment.promo_code_discount}",
            "Type": self._item,
            "No": "PROMOCODE",
            "ExpectedRevenue": Decimal(self._shipment.promo_code_discount) * Decimal("-1")
        }

        if is_account:
            billable["LocationCode"] = self._shipment.subaccount.bc_location_code
        else:
            billable["LocationCode"] = self._bc_location
            billable["UserID"] = self._bc_username

        self._request_list.append(billable)

    def _build_account(self):
        """

            :return:
        """

        for leg in self._shipment.leg_shipment.all():

            if leg.service_code == "PICK_DEL":
                continue

            sub_total = leg.cost - leg.tax
            revenue_amount = sub_total * (self._one + (leg.markup / self._hundred))
            o_province = leg.origin.province
            d_province = leg.destination.province
            origin_city = BBECityAlias.check_alias(
                alias=leg.origin.city, province_code=o_province.code, country_code=o_province.country.code
            )

            destination_city = BBECityAlias.check_alias(
                alias=leg.destination.city, province_code=d_province.code, country_code=d_province.country.code
            )

            self._request_list.append({
                "FunctionName": "AddJobPlanningLine",
                "JobNo": self._job_number,
                "LineType": self._shipment.subaccount.bc_line_type,
                "LegID": leg.leg_id,
                "LineID": leg.leg_id,
                "Description": f'{leg.leg_id}: {leg.carrier.get_mode_display()} - {origin_city} to {destination_city}'[:50],
                "Type": self._item,
                "No": self._shipment.subaccount.bc_item,
                "ExpectedVendorNo": leg.carrier.bc_vendor_code,
                "VendorReferenceNo": leg.tracking_identifier if leg.tracking_identifier else self._shipment.shipment_id,
                "ExpectedCost": sub_total,
                "MarkupPercentage": leg.markup,
                "ExpectedRevenue": Decimal(revenue_amount).quantize(Decimal("0.01")),
                "LocationCode": self._shipment.subaccount.bc_location_code,
            })

    def _send_requests(self) -> list:
        """
            Send requests to business central.
            :return:
        """
        response_list = []

        for request in self._request_list:
            response = self._post(request=request)
            response_list.append(response)

        return response_list

    def create_planning_lines(self) -> list:
        """
            Create new Job Planning Lines.
            :return: list of responses
        """

        if not self._job_number:
            raise BusinessCentralError(message="Customer Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            self._build_requests()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_planning.py line: 133", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to build job planning line request. (Planning Line)",
                data=str(e.message)
            )

        if self._shipment.insurance_amount > Decimal("0") and self._shipment.insurance_cost > Decimal("0"):
            self._build_insurance(is_account=False)

        if self._shipment.promo_code:
            self._build_promo(is_account=True)

        # Post Data to Business Central
        try:
            responses = self._send_requests()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_planning.py line: 144", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to send job planning line request.(SEND)", data=str(e.message)
            )

        return responses

    def create_account_planning_lines(self) -> list:
        """
            Create new Job Planning Lines.
            :return: list of responses
        """

        if not self._job_number:
            raise BusinessCentralError(message="Customer Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            self._build_account()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_planning.py line: 133", message=str(self._planning_lines))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to build job planning line request. (Planning Line)",
                data=str(e.message)
            )

        if self._shipment.insurance_amount > Decimal("0") and self._shipment.insurance_cost > Decimal("0"):
            self._build_insurance(is_account=True)

        if self._shipment.promo_code:
            self._build_promo(is_account=True)

        # Post Data to Business Central
        try:
            responses = self._send_requests()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_planning.py line: 144", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to send job planning line request.(SEND)", data=str(e.message)
            )

        return responses
