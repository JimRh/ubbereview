"""
    Title: Metric breakdown Api views
    Description: This file will contain all functions for Metric Carrier Api.
    Created: Nov 24, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.core.cache import cache

from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.metric_v3.metric_bbe_shipment_breakdown_v1 import GetMetricBBEShipmentBreakdown
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import SubAccount
from api.utilities.utilities import Utility
from brain.settings import FIVE_HOURS_CACHE_TTL


class MetricBreakdownApi(UbbeMixin, APIView):
    """
        Get a Metric breakdown.
    """

    # todo - Do properly serializer for response.

    @staticmethod
    def _get_cached_data(metrics: GetMetricBBEShipmentBreakdown, sub_account: SubAccount, params: dict, metric_type: str) -> dict:
        """
            Get cached data for metric
            :param metrics: Metric Class
            :param sub_account: sub account for request
            :param params: Filter params
            :return: Cached data
        """
        lookup_key = f'{metric_type}_{sub_account.subaccount_number}_{params["year"]}'

        # Check redis and cache metrics
        metric_data = cache.get(lookup_key)

        if not metric_data:
            metric_data = metrics.get_metrics(sub_account=sub_account, params=params)

        # Store metrics for 5 hours
        cache.set(lookup_key, metric_data, FIVE_HOURS_CACHE_TTL)

        return metric_data

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'year', openapi.IN_QUERY, description="Example: 2022", type=openapi.TYPE_STRING, required=False
            ),
        ],
        operation_id='Get Metric Breakdown',
        operation_description='Get metric breakdown of shipments for an account.',
        responses={
            '200': "Metric data",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Metric Carrier Overview.
            :param request: request
            :return: Json list of markups.
        """
        params = {}

        if 'year' in self.request.GET:
            params["year"] = self.request.GET.get("year")
        else:
            params["year"] = datetime.datetime.now().year

        metrics = GetMetricBBEShipmentBreakdown()

        try:
            metric_data = self._get_cached_data(
                metrics=metrics, sub_account=self._sub_account, params=params, metric_type="breakdown"
            )
        except ViewException as e:
            connection.close()
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=metric_data)
