"""
    Title: Metric Accounts Api views
    Description: This file will contain all functions for Metric Accounts Api.
    Created: Oct 7, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.metric_v3.metric_accounts_v3 import GetMetricAccounts
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import SubAccount
from api.utilities.utilities import Utility
from brain.settings import FIVE_HOURS_CACHE_TTL


class MetricAccountsApi(UbbeMixin, APIView):
    """
        Get a metric Accounts overview.
    """

    # todo - Do properly serializer for response.

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
                'system',
                openapi.IN_QUERY,
                description="ubbe (UB), Fetchable (FE), DeliverEase (DE), or Thrid Party (TP)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'year', openapi.IN_QUERY, description="Example: 2022", type=openapi.TYPE_INTEGER, required=True
            )
        ],
        operation_id='Get Metric Accounts Overview',
        operation_description='Get metric accounts overview which includes summary of shipments, packages, weight, '
                              'revenue, expense, and net profit.',
        responses={
            '200': "Metric data",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Metric Accounts Overview.
            :param request: request
            :return: Json list of account metrics.
        """
        errors = []

        account = self.request.GET.get("account")
        system = self.request.GET.get("system")
        year = self.request.GET.get("year")

        if not account:
            errors.append({"account": "Param: 'account' is required "})

        if not system:
            errors.append({"account": "Param: 'system' is required "})

        if not year:
            errors.append({"account": "Param: 'year' is required "})

        if errors:
            return Utility.json_error_response(code="6600", message="Metric Account: Invalid params.", errors=errors)

        try:
            sub_account = SubAccount.objects.get(subaccount_number=account)
        except ObjectDoesNotExist:
            connection.close()
            errors.append({"account": "Account Not found."})
            return Utility.json_error_response(code="6601", message="Metric Account: Account Not found.", errors=errors)

        # Get data for non bbe account.
        if not sub_account.is_bbe:
            errors.append({"account": "Permission denied."})
            return Utility.json_error_response(code="6602", message="Metric Account: Permission denied.", errors=errors)

        lookup_key = f'metric_account_{system}_{str(year)}'

        # Check redis and cache metrics
        metric_data = cache.get(lookup_key)

        if not metric_data:
            try:
                metric_data = GetMetricAccounts().get_metrics(params={"year": year, "system": system})
            except ViewException as e:
                connection.close()
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        # Store metrics for 5 hours
        cache.set(lookup_key, metric_data, FIVE_HOURS_CACHE_TTL)

        return Utility.json_response(data=metric_data)
