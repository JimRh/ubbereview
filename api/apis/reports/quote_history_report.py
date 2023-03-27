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


class QuoteHistoryReport:
    """
        Quote History Report for all modes of transportation
    """
    _zero = Decimal("0.00")

    headings = [
        "id",
        "Rate Date",
        "Account",
        "Origin City",
        "Origin Postal",
        "Origin Province",
        "Destination City",
        "Destination Postal",
        "Destination Province",
        "Total Quantity",
        "Total Weight",
        "Carrier",
        "Service",
        "Freight",
        "Surcharges",
        "Tax",
        "Total",
    ]

    @staticmethod
    def _process_data(response_data: dict, skip_carriers: list) -> list:
        rates = []

        for rate in response_data["rates"]:

            for mid in rate["middle"]:
                if mid["service_code"] == "BBEQUO":
                    continue

                if rate["carrier_id"] in skip_carriers:
                    continue

                new = copy.deepcopy(mid)
                new.update({"carrier_id": rate["carrier_id"], "carrier_name": rate["carrier_name"]})
                rates.append(new)

        rates = sorted(rates, key=lambda k: Decimal(k["total"]))

        return rates

    def _get_log_data(self, rate_logs: QuerySet, skip_carriers: list, mode: str = "NA") -> list:
        ret = []

        for log in rate_logs:

            if log.response_data:
                rates = self._process_data(response_data=log.response_data, skip_carriers=skip_carriers)
            else:
                rates = []

            total_quantity = sum(pack['quantity'] for pack in log.rate_data.get("packages", []))
            total_weight = sum(Decimal(pack['quantity']) * Decimal(pack['weight']) for pack in log.rate_data.get("packages", []))

            if rates:
                for rate in rates:
                    ret.append([
                        log.id,
                        log.rate_date.isoformat(),
                        log.sub_account.contact.company_name,
                        log.rate_data["origin"].get("city", ""),
                        log.rate_data["origin"].get("postal_code", ""),
                        log.rate_data["origin"].get("province", ""),
                        log.rate_data["destination"].get("city", ""),
                        log.rate_data["destination"].get("postal_code", ""),
                        log.rate_data["destination"].get("province", ""),
                        total_quantity,
                        total_weight,
                        rate.get("carrier_name", ""),
                        rate.get("service_name", ""),
                        rate.get("freight", ""),
                        rate.get("surcharge", ""),
                        rate.get("tax", ""),
                        rate.get("total", ""),
                    ])
            else:
                if mode == "NA":
                    ret.append([
                        log.id,
                        log.rate_date.isoformat(),
                        log.sub_account.contact.company_name,
                        log.rate_data["origin"].get("city", ""),
                        log.rate_data["origin"].get("postal_code", ""),
                        log.rate_data["origin"].get("province", ""),
                        log.rate_data["destination"].get("city", ""),
                        log.rate_data["destination"].get("postal_code", ""),
                        log.rate_data["destination"].get("province", ""),
                        total_quantity,
                        total_weight,
                        "",
                        "",
                        "",
                        "",
                        "",
                        ""
                    ])

        return ret

    def get_rate_log(self, rate_logs: QuerySet, file_name: str, mode: str):
        """
            Get Quote History Report for all modes of transportation data.
            :return: list of rate log data.
        """
        skip_carriers = set(
            list(AIR_CARRIERS) +
            list(COURIERS_CARRIERS) +
            list(LTL_CARRIERS) +
            list(FTL_CARRIERS) +
            list(SEALIFT_CARRIERS)
        )

        if mode == "AI":
            skip_carriers = skip_carriers.difference(list(AIR_CARRIERS))
        elif mode == "CO":
            skip_carriers = skip_carriers.difference(list(COURIERS_CARRIERS))
        elif mode == "LT":
            skip_carriers = skip_carriers.difference(list(LTL_CARRIERS))
        elif mode == "FT":
            skip_carriers = skip_carriers.difference(list(FTL_CARRIERS))
        elif mode == "SE":
            skip_carriers = skip_carriers.difference(list(SEALIFT_CARRIERS))
        else:
            skip_carriers = set()

        ret = self._get_log_data(rate_logs=rate_logs, skip_carriers=list(skip_carriers), mode=mode)
        sheet = ExcelReport(headings=self.headings, data=ret).create_report()

        return {
            "type": "excel",
            "file": sheet,
            "filename": file_name
        }
