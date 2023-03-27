"""
    Title: Quote History Report for all modes of transportation
    Description: The class filter requested filters and return thee following:
        - Start Date
        - End Date
    Created: August 19, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.db.models import QuerySet

from api.apis.reports.report_types.excel_report import ExcelReport
from api.globals.carriers import AIR_CARRIERS, COURIERS_CARRIERS, LTL_CARRIERS, FTL_CARRIERS, SEALIFT_CARRIERS


class AccountReport:
    """
        Quote History Report for all modes of transportation
    """
    _zero = Decimal("0.00")

    headings = [
        "id",
        "Account Number",
        "Creation Date",
        "System",
        "Account Name",
        "Contact",
        "Phone",
        "Email",
        "Address",
        "City",
        "Province",
        "Country",
        "Postal",
        "Tier",
        "Default Carrier Markup (%)",
        "BC File Type",
        "BC Customer Code",
        "BC Job Number",
        "BC Location Codee",
        "BC Line Type",
        "BC Item",
        "BC File Owner",
        "BC Active?",
        "Dangerous Goods?",
        "Pharma?",
        "Included in Metric?",
        "BBE Account"
    ]

    @staticmethod
    def _get_account_data(accounts: QuerySet) -> list:
        ret = []

        for account in accounts:

            ret.append([
                account.id,
                str(account.subaccount_number),
                account.creation_date.strftime("%Y-%m-%d"),
                account.get_system_display(),
                account.contact.company_name,
                account.contact.name,
                account.contact.phone,
                account.contact.email,
                account.address.address,
                account.address.city,
                account.address.province.code,
                account.address.province.country.code,
                account.address.postal_code,
                account.tier.name,
                account.markup.default_carrier_percentage,
                account.get_bc_type_display(),
                account.bc_customer_code,
                account.bc_job_number,
                account.bc_location_code,
                account.bc_line_type,
                account.bc_item,
                account.bc_file_owner,
                "Yes" if account.is_bc_push else "No",
                "Yes" if account.is_dangerous_good else "No",
                "Yes" if account.is_pharma else "No",
                "Yes" if account.is_metric_included else "No",
                "Yes" if account.is_bbe else "No"
            ])

        return ret

    def get_rate_log(self, accounts: QuerySet, file_name: str):
        """
            Get Quote History Report for all modes of transportation data.
            :return: list of rate log data.
        """

        account_data = self._get_account_data(accounts=accounts)

        sheet = ExcelReport(headings=self.headings, data=account_data).create_report()

        return {
            "type": "excel",
            "file": sheet,
            "filename": file_name
        }
