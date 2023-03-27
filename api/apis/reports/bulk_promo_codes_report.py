"""
    Title: Quote History Report separated by leg (mode)
    Description: The class filter requested filters and return thee following:
        - Start Date
        - End Date
    Created: April 26, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.db.models import QuerySet

from api.apis.reports.report_types.excel_report import ExcelReport
from api.globals.carriers import LTL_CARRIERS, AIR_CARRIERS, COURIERS_CARRIERS, UBBE_ML, UBBE_INTERLINE


class BulkPromoCodesReport:
    """
        Bulk Promo Codes Report
    """
    _zero = Decimal("0.00")

    headings = [
      "code"
    ]

    def get_bulk(self, file_name: str, bulk_list: list):
        """
            Get Bulk Promo Codes Report Data.
            :return: list of bulk promo codes data.
        """

        sheet = ExcelReport(headings=self.headings, data=bulk_list).create_report()

        return {
            "type": "excel",
            "file": sheet,
            "filename": file_name
        }
