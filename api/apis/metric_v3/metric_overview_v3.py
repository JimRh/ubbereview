"""
    Title: Metric Overview v3
    Description: The class filter requested filters and return thee following:
        - Start date
        - End date
        - Account
    Created: Sept 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection
from django.db.models import Sum, F

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, MetricAccount, SubAccount


class GetMetricOverview(MetricBase):
    """
        Metric Account Overview Api
    """

    def _get_account_data_from_filter(self, metric_data: dict):

        metric_data["shipments"] = self._get_value(metric_dict=metric_data, metric_key="shipments")
        metric_data["legs"] = self._get_value(metric_dict=metric_data, metric_key="legs")
        metric_data["air_legs"] = self._get_value(metric_dict=metric_data, metric_key="air_legs")
        metric_data["ltl_legs"] = self._get_value(metric_dict=metric_data, metric_key="ltl_legs")
        metric_data["ftl_legs"] = self._get_value(metric_dict=metric_data, metric_key="ftl_legs")
        metric_data["courier_legs"] = self._get_value(metric_dict=metric_data, metric_key="courier_legs")
        metric_data["sea_legs"] = self._get_value(metric_dict=metric_data, metric_key="sea_legs")
        metric_data["packages"] = self._get_value(metric_dict=metric_data, metric_key="packages")

        metric_data["weight"] = self._get_decimal_value(metric_dict=metric_data, metric_key="weight")
        metric_data["spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="spend")
        metric_data["air_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="air_spend")
        metric_data["ltl_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ltl_spend")
        metric_data["ftl_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ftl_spend")
        metric_data["courier_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="courier_spend")
        metric_data["sea_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="sea_spend")

        return metric_data

    def _get_account_managed_stats(self, metrics):
        """

            :param metrics:
            :return:
        """

        metric_data = metrics.aggregate(
            shipments=Sum('managed_shipments'),
            legs=Sum(F('managed_air_legs') + F('managed_ltl_legs') + F('managed_ftl_legs') + F('managed_courier_legs') + F('managed_sea_legs')),
            air_legs=Sum('managed_air_legs'),
            ltl_legs=Sum('managed_ltl_legs'),
            ftl_legs=Sum('managed_ftl_legs'),
            courier_legs=Sum('managed_courier_legs'),
            sea_legs=Sum('managed_sea_legs'),
            packages=Sum('managed_quantity'),
            weight=Sum('managed_weight'),
            spend=Sum('managed_revenue'),
            air_spend=Sum('managed_air_revenue'),
            ltl_spend=Sum('managed_ltl_revenue'),
            ftl_spend=Sum('managed_ftl_revenue'),
            courier_spend=Sum('managed_courier_revenue'),
            sea_spend=Sum('managed_sea_revenue')
        )

        metric_data = self._get_account_data_from_filter(metric_data=metric_data)

        return metric_data

    def _get_account_unmanaged_data(self, metrics):
        """

            :param metrics:
            :return:
        """

        metric_data = metrics.aggregate(
            shipments=Sum('shipments'),
            legs=Sum(F('air_legs') + F('ltl_legs') + F('ftl_legs') + F('courier_legs') + F('sea_legs')),
            air_legs=Sum('air_legs'),
            ltl_legs=Sum('ltl_legs'),
            ftl_legs=Sum('ftl_legs'),
            courier_legs=Sum('courier_legs'),
            sea_legs=Sum('sea_legs'),
            packages=Sum('quantity'),
            weight=Sum('weight'),
            spend=Sum('revenue'),
            air_spend=Sum('air_revenue'),
            ltl_spend=Sum('ltl_revenue'),
            ftl_spend=Sum('ftl_revenue'),
            courier_spend=Sum('courier_revenue'),
            sea_spend=Sum('sea_revenue')
        )

        metric_data = self._get_account_data_from_filter(metric_data=metric_data)

        return metric_data

    def _get_account_data(self, sub_account: SubAccount, start_date: str, end_date: str, query_type: str) -> dict:
        """

            :return:
        """

        if start_date and end_date:
            start_date, end_date = self._get_dates(start_date=start_date, end_date=end_date)
            metrics = MetricAccount.objects.filter(sub_account=sub_account, creation_date__range=[start_date, end_date])
        else:
            metrics = MetricAccount.objects.filter(sub_account=sub_account)

        if query_type == "COM":
            managed_metric_data = self._get_account_managed_stats(metrics=metrics)
            metric_data = self._get_account_unmanaged_data(metrics=metrics)

            for key, value in managed_metric_data.items():
                metric_data[key] += value
        elif query_type == "MAN":
            metric_data = self._get_account_managed_stats(metrics=metrics)
        else:
            metric_data = self._get_account_unmanaged_data(metrics=metrics)

        return metric_data

    def _get_bbe_data_from_filter(self, metric_data: dict):

        metric_data["weight"] = self._get_decimal_value(metric_dict=metric_data, metric_key="weight")
        metric_data["spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="spend")
        metric_data["expense"] = self._get_decimal_value(metric_dict=metric_data, metric_key="expense")
        metric_data["net_profit"] = self._get_decimal_value(metric_dict=metric_data, metric_key="net_profit")
        metric_data["air_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="air_spend")
        metric_data["air_expense"] = self._get_decimal_value(metric_dict=metric_data, metric_key="air_expense")
        metric_data["air_net_profit"] = self._get_decimal_value(metric_dict=metric_data, metric_key="air_net_profit")
        metric_data["ltl_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ltl_spend")
        metric_data["ltl_expense"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ltl_expense")
        metric_data["ftl_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ftl_spend")
        metric_data["ftl_expense"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ftl_expense")
        metric_data["ftl_net_profit"] = self._get_decimal_value(metric_dict=metric_data, metric_key="ftl_net_profit")
        metric_data["courier_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="courier_spend")
        metric_data["courier_expense"] = self._get_decimal_value(metric_dict=metric_data, metric_key="courier_expense")
        metric_data["courier_net_profit"] = self._get_decimal_value(metric_dict=metric_data, metric_key="courier_net_profit")
        metric_data["sea_spend"] = self._get_decimal_value(metric_dict=metric_data, metric_key="sea_spend")
        metric_data["sea_expense"] = self._get_decimal_value(metric_dict=metric_data, metric_key="sea_expense")
        metric_data["sea_net_profit"] = self._get_decimal_value(metric_dict=metric_data, metric_key="sea_net_profit")

        return metric_data

    def _get_bbe_managed_stats(self, metrics):
        """

            :param metrics:
            :return:
        """

        metric_data = metrics.aggregate(
            shipments=Sum('managed_shipments'),
            legs=Sum(F('managed_air_legs') + F('ltl_legs') + F('ftl_legs') + F('courier_legs') + F('sea_legs')),
            air_legs=Sum('managed_air_legs'),
            ltl_legs=Sum('managed_ltl_legs'),
            ftl_legs=Sum('managed_ftl_legs'),
            courier_legs=Sum('managed_courier_legs'),
            sea_legs=Sum('managed_sea_legs'),
            packages=Sum('managed_quantity'),
            weight=Sum('managed_weight'),
            spend=Sum('managed_revenue'),
            expense=Sum('managed_expense'),
            net_profit=Sum('managed_net_profit'),
            air_spend=Sum('managed_air_revenue'),
            air_expense=Sum('managed_air_expense'),
            air_net_profit=Sum('managed_air_net_profit'),
            ltl_spend=Sum('managed_ltl_revenue'),
            ltl_expense=Sum('managed_ltl_expense'),
            ltl_net_profit=Sum('managed_ltl_net_profit'),
            ftl_spend=Sum('managed_ftl_revenue'),
            ftl_expense=Sum('managed_ftl_expense'),
            ftl_net_profit=Sum('managed_ftl_net_profit'),
            courier_spend=Sum('managed_courier_revenue'),
            courier_expense=Sum('managed_courier_expense'),
            courier_net_profit=Sum('managed_courier_net_profit'),
            sea_spend=Sum('managed_sea_revenue'),
            sea_expense=Sum('managed_sea_expense'),
            sea_net_profit=Sum('managed_sea_net_profit'),
        )

        metric_data = self._get_bbe_data_from_filter(metric_data=metric_data)

        return metric_data

    def get_bbe_unmanaged_data(self, metrics):
        """

            :param metrics:
            :return:
        """

        metric_data = metrics.aggregate(
            shipments=Sum('shipments'),
            legs=Sum(F('air_legs') + F('ltl_legs') + F('ftl_legs') + F('courier_legs') + F('sea_legs')),
            air_legs=Sum('air_legs'),
            ltl_legs=Sum('ltl_legs'),
            ftl_legs=Sum('ftl_legs'),
            courier_legs=Sum('courier_legs'),
            sea_legs=Sum('sea_legs'),
            packages=Sum('quantity'),
            weight=Sum('weight'),
            spend=Sum('revenue'),
            expense=Sum('expense'),
            net_profit=Sum('net_profit'),
            air_spend=Sum('air_revenue'),
            air_expense=Sum('air_expense'),
            air_net_profit=Sum('air_net_profit'),
            ltl_spend=Sum('ltl_revenue'),
            ltl_expense=Sum('ltl_expense'),
            ltl_net_profit=Sum('ltl_net_profit'),
            ftl_spend=Sum('ftl_revenue'),
            ftl_expense=Sum('ftl_expense'),
            ftl_net_profit=Sum('ftl_net_profit'),
            courier_spend=Sum('courier_revenue'),
            courier_expense=Sum('courier_expense'),
            courier_net_profit=Sum('courier_net_profit'),
            sea_spend=Sum('sea_revenue'),
            sea_expense=Sum('sea_expense'),
            sea_net_profit=Sum('sea_net_profit'),
        )

        metric_data = self._get_bbe_data_from_filter(metric_data=metric_data)

        return metric_data

    def _get_data(self, metrics, query_type: str):
        """

            :return:
        """

        if query_type == "COM":
            managed_metric_data = self._get_bbe_managed_stats(metrics=metrics)
            metric_data = self.get_bbe_unmanaged_data(metrics=metrics)

            for key, value in managed_metric_data.items():
                metric_data[key] += value

        elif query_type == "MAN":
            metric_data = self._get_bbe_managed_stats(metrics=metrics)
        else:
            metric_data = self.get_bbe_unmanaged_data(metrics=metrics)

        return metric_data

    def _get_bbe_data(self, sub_account: SubAccount, start_date: str, end_date: str, params: dict) -> dict:
        """

            :param sub_account:
            :param start_date:
            :param end_date:
            :param params:
            :return:
        """

        accounts = params.get("accounts", [])

        if accounts and start_date and end_date:
            start_date, end_date = self._get_dates(start_date=start_date, end_date=end_date)
            metrics = MetricAccount.objects.filter(
                creation_date__range=[start_date, end_date],
                sub_account__subaccount_number__in=accounts
            )
            return self._get_data(metrics=metrics, query_type=params["query_type"])
        elif accounts:
            metrics = MetricAccount.objects.filter(sub_account__subaccount_number__in=accounts)
            return self._get_data(metrics=metrics, query_type=params["query_type"])

        return self._get_account_data(
            sub_account=sub_account, start_date=start_date, end_date=end_date, query_type=params["query_type"]
        )

    def get_metrics(self, sub_account: SubAccount, params: dict) -> dict:
        """
            Get Metric Account Overview. IE: Shipment Count, Leg Count, Package Count, and Weight Count.
            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="MetricOverviewV3").active:
            connection.close()
            errors.append({"metric_overview": "Metric endpoint not active."})
            raise ViewException(code="7103", message="MetricOverview: Endpoint not active.", errors=errors)

        start_date = params['start_date']
        end_date = params['end_date']
        query_type = params['query_type']

        if (start_date and not end_date) or (not start_date and end_date):
            connection.close()
            errors.append({"dates": "'start_date' and 'end_date' are both required if one occurs."})
            errors.append({"start_date": "Must be in '%Y-%m-%d'"})
            errors.append({"end_date": "Must be in '%Y-%m-%d'"})
            raise ViewException(code="7104", message="MetricOverview: Invalid dates.", errors=errors)

        if sub_account.is_bbe:
            ret = self._get_bbe_data(sub_account=sub_account, start_date=start_date, end_date=end_date, params=params)
        else:
            ret = self._get_account_data(
                sub_account=sub_account, start_date=start_date, end_date=end_date, query_type=query_type
            )

        ret.update({
            "weight_units": "KG",
            "currency": "CAD",
            "last_updated": self._get_date(),
        })

        connection.close()
        return ret
