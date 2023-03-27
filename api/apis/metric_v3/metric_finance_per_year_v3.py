"""
    Title: Metric Finance Per Year v3
    Description: The class filter requested filters and return the following:
        - Start date
        - End date
        - Account
    Created: Sept 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection
from django.db.models import Sum, QuerySet

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, MetricAccount, SubAccount


class GetMetricFinancePerYear(MetricBase):
    """
        Metric Account Finance Per Year Api
    """

    def _get_per_data(self, years: list, metrics: QuerySet, query_type: str) -> list:
        """
            Get finance data per year and quarter.
            :return: list of year data
        """
        year_data = []

        for year in years:
            rev_data = []
            exp_data = []
            net_data = []

            for month in self._months:

                if query_type == "COM":
                    man_shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(
                        revenue=Sum("managed_revenue"),
                        expense=Sum("managed_expense"),
                        net_profit=Sum("managed_net_profit")
                    )

                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(revenue=Sum("revenue"), expense=Sum("expense"), net_profit=Sum("net_profit"))

                    revenue = self._get_decimal_value(metric_dict=shipment_data, metric_key="revenue")
                    expense = self._get_decimal_value(metric_dict=shipment_data, metric_key="expense")
                    net_profit = self._get_decimal_value(metric_dict=shipment_data, metric_key="net_profit")

                    man_revenue = self._get_decimal_value(metric_dict=man_shipment_data, metric_key="revenue")
                    man_expense = self._get_decimal_value(metric_dict=man_shipment_data, metric_key="expense")
                    man_net_profit = self._get_decimal_value(metric_dict=man_shipment_data, metric_key="net_profit")

                    shipment_data["revenue"] = revenue + man_revenue
                    shipment_data["expense"] = expense + man_expense
                    shipment_data["net_profit"] = net_profit + man_net_profit

                elif query_type == "MAN":
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(
                        revenue=Sum("managed_revenue"),
                        expense=Sum("managed_expense"),
                        net_profit=Sum("managed_net_profit")
                    )
                else:
                    shipment_data = metrics.filter(
                        creation_date__year=year, creation_date__month=month
                    ).aggregate(revenue=Sum("revenue"), expense=Sum("expense"), net_profit=Sum("net_profit"))

                revenue = self._get_decimal_value(metric_dict=shipment_data, metric_key="revenue")
                expense = self._get_decimal_value(metric_dict=shipment_data, metric_key="expense")
                net_profit = self._get_decimal_value(metric_dict=shipment_data, metric_key="net_profit")

                rev_data.append(revenue.quantize(self._sig_fig))
                exp_data.append(expense.quantize(self._sig_fig))
                net_data.append(net_profit.quantize(self._sig_fig))

            year_data.append({
                "year": year,
                "month_revenue": rev_data,
                "month_expense": exp_data,
                "month_net_profit": net_data
            })

        return year_data

    def _get_account_data(self, sub_account: SubAccount, year_list: list, query_type: str) -> list:
        """
            Get Account data.
            :param sub_account: Account sub account.
            :param year_list: year list
            :return: list of shipments per year
        """

        metrics = MetricAccount.objects.filter(sub_account=sub_account)

        return self._get_per_data(years=year_list, metrics=metrics, query_type=query_type)

    def _get_bbe_data(self, sub_account: SubAccount, year_list: list, params: dict) -> list:
        """
            Get BBE specific data. includes all shipment filter
            :param sub_account: Account sub account.
            :param year_list: year list
            :param params:
            :return: list of shipments per year
        """
        accounts = params.get("accounts", [])

        if accounts:
            metrics = MetricAccount.objects.filter(sub_account__subaccount_number__in=accounts)
            return self._get_per_data(years=year_list, metrics=metrics, query_type=params["query_type"])

        return self._get_account_data(sub_account=sub_account, year_list=year_list, query_type=params["query_type"])

    def get_metrics(self, sub_account: SubAccount, params: dict) -> dict:
        """
            Get metrics for shipments per year for an account or if BBE all accounts. Also can override years.
            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="MetricFinancePerYearV3").active:
            connection.close()
            errors.append({"metric_finance_per_year": "Metric endpoint not active."})
            raise ViewException(code="6904", message="MetricFinancePerYear: Endpoint not active.", errors=errors)

        year_list = params["years"]
        query_type = params["query_type"]

        if not year_list:
            year_list = self._get_default_years()

        if sub_account.is_bbe:
            year_data = self._get_bbe_data(sub_account=sub_account, year_list=year_list, params=params)
        else:
            year_data = self._get_account_data(sub_account=sub_account, year_list=year_list, query_type=query_type)

        ret = {
            "years": year_data,
            "months": self._month_name_str,
            "last_updated": self._get_date()
        }

        return ret
