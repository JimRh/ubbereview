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


class QuoteHistoryByLegReport:
    """
        Quote History Report separated by leg (mode)
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
        "Air Cheapest Carrier",
        "Air Cheapest",
        "Air Middle Carrier",
        "Air Middle",
        "Air Most Expensive Carrier",
        "Air Most Expensive",
        "Courier Cheapest Carrier",
        "Courier Cheapest",
        "Courier Middle Carrier",
        "Courier Middle",
        "Courier Most Expensive Carrier",
        "Courier Most Expensive",
        "LTL Cheapest Carrier",
        "LTL Cheapest",
        "LTL Middle Carrier",
        "LTL Middle",
        "LTL Most Expensive Carrier",
        "LTL Most Expensive",
        "ubbe ML Cost"
    ]

    @staticmethod
    def _get_cheapest(rate_data: list) -> dict:
        """

            :param rate_data:
            :return:
        """

        if not rate_data:
            return {}

        rate = min(rate_data, key=lambda l: Decimal(l["total"]))
        return rate

    @staticmethod
    def _get_most_expensive(rate_data: list) -> dict:
        """

            :param rate_data:
            :return:
        """

        if not rate_data:
            return {}

        rate = max(rate_data, key=lambda l: Decimal(l["total"]))
        return rate

    def _get_log_data(self, rate_logs: QuerySet) -> list:
        ret = []

        for log in rate_logs:

            if log.response_data:
                air_data, courier_data, ltl_data, ubbe_ml = self._process_data(response_data=log.response_data)
            else:
                air_data = {}
                courier_data = {}
                ltl_data = {}
                ubbe_ml = {}

            total_quantity = sum(pack['quantity'] for pack in log.rate_data.get("packages", []))
            total_weight = sum(Decimal(pack['quantity']) * Decimal(pack['weight']) for pack in log.rate_data.get("packages", []))

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
                air_data.get("cheapest", {}).get("carrier_name", ""),
                air_data.get("cheapest", {}).get("total", ""),
                air_data.get("middle", {}).get("carrier_name", ""),
                air_data.get("middle", {}).get("total", ""),
                air_data.get("expensive", {}).get("carrier_name", ""),
                air_data.get("expensive", {}).get("total", ""),
                courier_data.get("cheapest", {}).get("carrier_name", ""),
                courier_data.get("cheapest", {}).get("total", ""),
                courier_data.get("middle", {}).get("carrier_name", ""),
                courier_data.get("middle", {}).get("total", ""),
                courier_data.get("expensive", {}).get("carrier_name", ""),
                courier_data.get("expensive", {}).get("total", ""),
                ltl_data.get("cheapest", {}).get("carrier_name", ""),
                ltl_data.get("cheapest", {}).get("total", ""),
                ltl_data.get("middle", {}).get("carrier_name", ""),
                ltl_data.get("middle", {}).get("total", ""),
                ltl_data.get("expensive", {}).get("carrier_name", ""),
                ltl_data.get("expensive", {}).get("total", ""),
                ubbe_ml.get("total", "")
            ])

        return ret

    def _process_data(self, response_data: dict) -> tuple:
        air = []
        courier = []
        ltl = []

        ubbe_ml = {}
        air_data = {}
        courier_data = {}
        ltl_data = {}

        for rate in response_data["rates"]:

            for mid in rate["middle"]:

                if mid["service_code"] == "BBEQUO":
                    continue

                new = copy.deepcopy(mid)
                new.update({"carrier_id": rate["carrier_id"], "carrier_name": rate["carrier_name"]})

                if rate["carrier_id"] == UBBE_ML:
                    ubbe_ml = new
                elif rate["carrier_id"] in AIR_CARRIERS:
                    air.append(new)
                elif rate["carrier_id"] in COURIERS_CARRIERS:
                    courier.append(new)
                elif rate["carrier_id"] in LTL_CARRIERS or rate["carrier_id"] in [UBBE_ML, UBBE_INTERLINE]:
                    ltl.append(new)

        air_data["cheapest"] = self._get_cheapest(rate_data=air)
        courier_data["cheapest"] = self._get_cheapest(rate_data=courier)
        ltl_data["cheapest"] = self._get_cheapest(rate_data=ltl)

        if air:
            air = sorted(air, key=lambda k: Decimal(k["total"]))
            air_data["middle"] = air[len(air) // 2]

        if courier:
            courier = sorted(courier, key=lambda k: Decimal(k["total"]))
            courier_data["middle"] = courier[len(courier) // 2]

        if ltl:
            ltl = sorted(ltl, key=lambda k: Decimal(k["total"]))
            ltl_data["middle"] = ltl[len(ltl) // 2]

        air_data["expensive"] = self._get_most_expensive(rate_data=air)
        courier_data["expensive"] = self._get_most_expensive(rate_data=courier)
        ltl_data["expensive"] = self._get_most_expensive(rate_data=ltl)

        return air_data, courier_data, ltl_data, ubbe_ml

    def get_rate_log(self, rate_logs: QuerySet, file_name: str):
        """
            Get Quote History Report separated by leg (mode) data.
            :return: list of rate log data.
        """
        ret = self._get_log_data(rate_logs=rate_logs)

        sheet = ExcelReport(headings=self.headings, data=ret).create_report()

        return {
            "type": "excel",
            "file": sheet,
            "filename": file_name
        }
