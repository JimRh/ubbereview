"""
    Title: Metric Carriers v3
    Description: The class filter requested filters and return thee following:
        - Start date
        - End date
        - Account
    Created: Sept 28, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db import connection
from django.db.models import Count
from django.db.models.aggregates import Sum
from django.db.models.expressions import F

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, SubAccount, Shipment, Leg


class GetMetricBBEShipmentBreakdown(MetricBase):
    """
        Metric BBE Shipment Breakdown.
    """

    def _get_data(self, sub_account: SubAccount, params: dict):
        """

            :return:
        """

        shipments = Shipment.objects.filter(
            is_shipped=True, subaccount=sub_account, creation_date__year=params["year"]
        ).values(
            'bc_customer_code', 'bc_customer_name'
        ).annotate(amount=Count('bc_customer_code')).order_by('-amount')

        customers = self._get_value(
            metric_dict=shipments.aggregate(Count('bc_customer_code')), metric_key="bc_customer_code__count"
        )

        total = self._get_value(
            metric_dict=shipments.aggregate(Sum('amount')), metric_key="amount__sum"
        )

        ret = {
            "breakdown": list(shipments),
            "customers": customers,
            "amount": total,
        }

        return ret

    def _get_additional_metrics(self, sub_account, data: dict):
        """

            :param data:
            :return:
        """
        total_expense = Decimal("0")
        total_revenue = Decimal("0")
        total_net = Decimal("0")

        for breakdown in data["breakdown"]:

            leg_data = Leg.objects.filter(
                shipment__subaccount=sub_account,
                shipment__bc_customer_code=breakdown["bc_customer_code"],
                shipment__bc_customer_name=breakdown["bc_customer_name"],
                shipment__creation_date__year=2022
            ).aggregate(
                expense=Sum(F('base_cost') - F('base_tax')),
                revenue=Sum((F('base_cost') - F('base_tax')) * ((F('markup') / 100) + 1)),
            )

            expense = self._get_decimal_value(metric_dict=leg_data, metric_key="expense")
            revenue = self._get_decimal_value(metric_dict=leg_data, metric_key="revenue")
            net = revenue - expense

            total_expense += expense
            total_revenue += revenue
            total_net += net

            breakdown.update({
                "expense": expense,
                "revenue": revenue,
                "net": net,
            })

        data.update({
            "total_expense": total_expense,
            "total_revenue": total_revenue,
            "total_net": total_net
        })

    def get_metrics(self, sub_account: SubAccount, params: dict) -> dict:
        """
            Get Metric Routes. IE: City Count and Province Count.
            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="GetMetricBBEShipmentBreakdownV1").active:
            connection.close()
            errors.append({"metric_carriers": "Metric endpoint not active."})
            raise ViewException(code="6803", message="Metric BBEShipmentBreakdown: Endpoint not active.", errors=errors)

        if not sub_account.is_bbe:
            errors.append({"metric_carriers": "Metric endpoint not active."})
            raise ViewException(code="6803", message="Metric BBEShipmentBreakdown: Endpoint not active.", errors=errors)

        ret = self._get_data(sub_account=sub_account, params=params)
        self._get_additional_metrics(sub_account=sub_account, data=ret)

        ret.update({
            "last_updated": self._get_date(),
        })

        connection.close()
        return ret
