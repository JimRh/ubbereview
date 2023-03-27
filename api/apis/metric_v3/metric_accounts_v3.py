"""
    Title: Metric Accounts v3
    Description: The class filter requested filters and return thee following:
        - System
        - Year
    Created: Oct 7, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db import connection
from django.db.models import Sum

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, MetricAccount, SubAccount


class GetMetricAccounts(MetricBase):
    """
        Metric Accounts Overview Api
    """

    def _get_account_data(self, params: dict) -> list:
        """

            :return:
        """
        metric_list = []
        system = params["system"]
        year = params["year"]

        sub_accounts = SubAccount.objects.filter(system=system)

        for sub_account in sub_accounts:
            metrics = MetricAccount.objects.filter(sub_account=sub_account, creation_date__year=year)

            metric_data = metrics.aggregate(
                shipments=Sum('shipments'),
                packages=Sum('quantity'),
                weight=Sum('weight'),
                revenue=Sum('revenue'),
                expense=Sum('expense'),
                net_profit=Sum('net_profit'),
                managed_shipments=Sum('managed_shipments'),
                managed_packages=Sum('managed_quantity'),
                managed_weight=Sum('managed_weight'),
                managed_revenue=Sum('managed_revenue'),
                managed_expense=Sum('managed_expense'),
                managed_net_profit=Sum('managed_net_profit'),
            )

            for key in ["shipments", "packages", "weight", "revenue", "expense", "net_profit"]:
                metric_data[key] = self._get_value(metric_dict=metric_data, metric_key=key)
                metric_data[f"managed_{key}"] = self._get_value(metric_dict=metric_data, metric_key=f"managed_{key}")

            metric_data.update({
                "account": sub_account.contact.company_name,
                "system": sub_account.get_system_display(),
            })

            metric_list.append(metric_data)

        return metric_list

    def _sum_metric_list(self, metric_list) -> dict:
        """

            :param metric_list:
            :return:
        """
        ret = {
            "accounts": 0,
            "shipments": 0,
            "packages": 0,
            "weight": self._decimal_zero,
            "revenue": self._decimal_zero,
            "expense": self._decimal_zero,
            "net_profit": self._decimal_zero,
            "managed_shipments": 0,
            "managed_packages": 0,
            "managed_weight": self._decimal_zero,
            "managed_revenue": self._decimal_zero,
            "managed_expense": self._decimal_zero,
            "managed_net_profit": self._decimal_zero
        }

        for metric in metric_list:
            ret["accounts"] += 1
            ret["shipments"] = ret["shipments"] + metric["shipments"]
            ret["packages"] = ret["packages"] + metric["packages"]
            ret["weight"] = Decimal(ret["weight"] + metric["weight"]).quantize(self._sig_fig)
            ret["revenue"] = Decimal(ret["revenue"] + metric["revenue"]).quantize(self._sig_fig)
            ret["expense"] = Decimal(ret["expense"] + metric["expense"]).quantize(self._sig_fig)
            ret["net_profit"] = Decimal(ret["net_profit"] + metric["net_profit"]).quantize(self._sig_fig)

            ret["managed_shipments"] = ret["managed_shipments"] + metric["managed_shipments"]
            ret["managed_packages"] = ret["managed_packages"] + metric["managed_packages"]
            ret["managed_weight"] = Decimal(ret["managed_weight"] + metric["managed_weight"]).quantize(self._sig_fig)
            ret["managed_revenue"] = Decimal(ret["managed_revenue"] + metric["managed_revenue"]).quantize(self._sig_fig)
            ret["managed_expense"] = Decimal(ret["managed_expense"] + metric["managed_expense"]).quantize(self._sig_fig)
            ret["managed_net_profit"] = Decimal(ret["managed_net_profit"] + metric["managed_net_profit"]).quantize(
                self._sig_fig
            )

        return ret

    def get_metrics(self, params: dict) -> dict:
        """
            Get Metric Account Overview. IE: Shipment Count, Package Count, Weight Count, Costs.

            BBE ONLY METRIC

            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="MetricAccountsV3").active:
            connection.close()
            errors.append({"metric_account": "Metric endpoint not active."})
            raise ViewException(code="6603", message="Metric Account: Endpoint not active.", errors=errors)

        metric_list = self._get_account_data(params=params)
        metric_list = sorted(metric_list, key=lambda k: k['revenue'])[::-1]
        sum_data = self._sum_metric_list(metric_list=metric_list)

        connection.close()
        return {
            "metric_list": metric_list,
            "summary": sum_data,
            "weight_units": "KG",
            "currency": "CAD",
            "last_updated": self._get_date(),
        }
