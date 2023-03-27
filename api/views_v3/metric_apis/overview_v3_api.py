"""
    Title: Metric Account Api views
    Description: This file will contain all functions for Metric Account Api.
    Created: Sept 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import simplejson as json
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.metric_v3.metric_overview_v3 import GetMetricOverview
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import SubAccount
from api.utilities.utilities import Utility
from brain.settings import FIVE_HOURS_CACHE_TTL


class MetricOverviewApi(UbbeMixin, APIView):
    """
        Get a metric account overview.
    """

    # todo - Do properly serializer for response.

    @staticmethod
    def _get_cached_data(metrics: GetMetricOverview, sub_account: SubAccount, params: dict, metric_type: str) -> dict:
        """
            Get cached data for metric
            :param metrics: Metric Class
            :param sub_account: sub account for request
            :param params: Filter params
            :return: Cached data
        """
        lookup_key = f'{metric_type}_{sub_account.subaccount_number}_{params["start_date"]}_{params["end_date"]}_{params["query_type"]}'

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
                'account',
                openapi.IN_QUERY,
                description="Sub Account Number",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            ),
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="Example: 2022", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="Example: 2022", type=openapi.TYPE_STRING, required=True
            )
        ],
        operation_id='Get Metric Overview',
        operation_description='Get metric overview which includes revenue, expense, net profit broken down by mode',
        responses={
            '200': "Metric data",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Metric Overview.
            :param request: request
            :return: Json list of markups.
        """
        errors = []
        account = self.request.GET.get("account", "")
        params = {
            "start_date": self.request.GET.get("start_date"),
            "end_date": self.request.GET.get("end_date"),
            "query_type": self.request.GET.get("query_type", "UMAN")
        }

        if not account:
            connection.close()
            errors.append({"account": "Param: 'account' is required "})
            return Utility.json_error_response(code="7100", message="MetricOverview: Invalid params.", errors=errors)

        try:
            sub_account = SubAccount.objects.get(subaccount_number=account)
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"account": "Account Not found."})
            return Utility.json_error_response(code="7101", message="MetricOverview: Account Not found.", errors=errors)

        metric_overview = GetMetricOverview()

        # Get data for non bbe account.
        if not sub_account.is_bbe:

            try:
                metric_data = self._get_cached_data(
                    metrics=metric_overview, sub_account=sub_account, params=params, metric_type="overview"
                )
            except ViewException as e:
                connection.close()
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            return Utility.json_response(data=metric_data)

        try:
            accounts = json.loads(self.request.GET.get("accounts", '[]'))
        except ValueError:
            errors.append({"accounts": "Must be json list or not included."})
            return Utility.json_error_response(code="6702", message="MetricOverview: Invalid param.", errors=errors)

        # Get data for only bbe account and cache it, otherwise don't cache all accounts lookups
        if not accounts:
            try:
                metric_data = self._get_cached_data(
                    metrics=metric_overview, sub_account=sub_account, params=params, metric_type="overview"
                )
            except ViewException as e:
                connection.close()
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            return Utility.json_response(data=metric_data)

        params["accounts"] = accounts

        try:
            metric_data = metric_overview.get_metrics(sub_account=sub_account, params=params)
        except ViewException as e:
            connection.close()
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=metric_data)
