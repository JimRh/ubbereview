"""
    Title: Metric Shipment Per Year v3
    Description: The class filter requested filters and return thee following:
        - Start date
        - End date
        - Account
    Created: Sept 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.db import connection
from django.db.models import Sum, QuerySet

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, MetricAccount, SubAccount


class GetMetricShipmentPerYear(MetricBase):
    """
        Metric Account Shipment Per Year Api
    """

    def _get_per_data(self, years: list, metrics: QuerySet, query_type: str) -> list:
        """
            Get shipment data per year and quarter.
            :return: list of year data
        """
        year_data = []
        now = datetime.datetime.now()

        for year in years:
            month_data = []
            quarter_data = []
            quarter_name = []

            for month in self._months:

                if query_type == "COM":
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(shipments=Sum("shipments"), managed_shipments=Sum("managed_shipments"))

                    shipment_count = self._get_value(metric_dict=shipment_data, metric_key="shipments")
                    man_count = self._get_value(metric_dict=shipment_data, metric_key="managed_shipments")

                    shipment_data["shipments"] = shipment_count + man_count
                elif query_type == "MAN":
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(shipments=Sum("managed_shipments"))
                else:
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(shipments=Sum("shipments"))

                if shipment_data["shipments"]:
                    month_data.append(shipment_data["shipments"])
                else:
                    if year == now.year and month > now.month:
                        continue

                    month_data.append(self._zero)

            for quarter, name in [self._q_one, self._q_two, self._q_three, self._q_four]:

                if query_type == "COM":
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month__in=quarter
                    ).aggregate(shipments=Sum("shipments"), managed_shipments=Sum("managed_shipments"))

                    shipment_count = self._get_value(metric_dict=shipment_data, metric_key="shipments")
                    man_count = self._get_value(metric_dict=shipment_data, metric_key="managed_shipments")

                    shipment_data["shipments"] = shipment_count + man_count
                elif query_type == "MAN":
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month__in=quarter
                    ).aggregate(shipments=Sum("managed_shipments"))
                else:
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month__in=quarter
                    ).aggregate(shipments=Sum("shipments"))

                quarter_data.append(shipment_data["shipments"] if shipment_data["shipments"] else self._zero)
                quarter_name.append(name)

            year_data.append({
                "year": year,
                "month_data": month_data,
                "quarter_data": quarter_data,
            })

        return year_data

    def _get_account_data(self, sub_account: SubAccount, year_list: list, query_type: str) -> list:
        """
            Get Account data.
            :param sub_account: Account sub account.
            :param year_list: year list
            :return: list of finances per year
        """

        metrics = MetricAccount.objects.filter(sub_account=sub_account)

        return self._get_per_data(years=year_list, metrics=metrics, query_type=query_type)

    def _get_bbe_data(self, sub_account: SubAccount, year_list: list, query_type: str, params: dict) -> list:
        """
            Get BBE specific data. includes all shipment filter
            :param sub_account: Account sub account.
            :param year_list: year list
            :param params: list of finances per year
            :return: list of finances per year
        """
        accounts = params.get("accounts", [])

        if accounts:
            metrics = MetricAccount.objects.filter(sub_account__subaccount_number__in=accounts)
            return self._get_per_data(years=year_list, metrics=metrics, query_type=query_type)

        return self._get_account_data(sub_account=sub_account, year_list=year_list, query_type=query_type)

    def get_metrics(self, sub_account: SubAccount, params: dict) -> dict:
        """
            Get metrics for finances per year for an account or if BBE all accounts. Also can override years.
            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="MetricShipmentPerYearV3").active:
            connection.close()
            errors.append({"metric_shipment_per_year": "Metric endpoint not active."})
            raise ViewException(code="7304", message="MetricShipmentPerYear: Endpoint not active.", errors=errors)

        year_list = params["years"]
        query_type = params["query_type"]

        if not year_list:
            year_list = self._get_default_years()

        if sub_account.is_bbe:
            year_data = self._get_bbe_data(
                sub_account=sub_account, year_list=year_list, query_type=query_type, params=params
            )
        else:
            year_data = self._get_account_data(sub_account=sub_account, year_list=year_list, query_type=query_type)

        ret = {
            "years": year_data,
            "months": self._month_name_str,
            "quarters": self._quarters,
            "last_updated": self._get_date()
        }

        return ret
