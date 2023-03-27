"""
    Title: Carrier Markup api views
    Description: This file will contain all functions for carrier serializers.
    Created: November 19, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.db import connection
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListAPIView

from api.apis.reports.quote_history_by_leg_report import QuoteHistoryByLegReport
from api.apis.reports.quote_history_report import QuoteHistoryReport
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import RateLog, API

# TODO - Should this be cached or not.
from api.utilities.utilities import Utility


class QuoteHistoryByLegReportApi(UbbeMixin, ListAPIView):
    http_method_names = ['get']

    # Customs
    _thirty_days = 30

    def get_queryset(self):
        """
            Get initial carrier markup history queryset and apply query params to the queryset.
            :return:
        """

        if 'end_date' in self.request.query_params:
            end_date = datetime.strptime(self.request.query_params["end_date"], "%Y-%m-%d").replace(tzinfo=utc)
        else:
            end_date = datetime.now().replace(tzinfo=utc)

        if 'start_date' in self.request.query_params:
            start_date = datetime.strptime(self.request.query_params["start_date"], "%Y-%m-%d").replace(tzinfo=utc)
        else:
            start_date = end_date - timedelta(days=self._thirty_days)

        if self._sub_account.is_bbe:
            logs = RateLog.objects.select_related("sub_account__contact").filter(
                rate_date__range=[start_date, end_date]
            )
        else:
            logs = RateLog.objects.select_related("sub_account__contact").filter(
                rate_date__range=[start_date, end_date],
                sub_account=self._sub_account
            )

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            logs = logs.filter(sub_account__subaccount_number=self.request.query_params["account"])

        if 'is_no_rate' in self.request.query_params:
            logs = logs.filter(is_no_rate=self.request.query_params["is_no_rate"])

        return logs.order_by('-rate_date')

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'account',
                openapi.IN_QUERY,
                description="Sub Account Number",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            )
        ],
        operation_id='Get Quote History By Leg Report',
        operation_description='Get a excel sheet of quoting history by leg.',
        responses={
            '200': 'excel sheet',
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier markup history for the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if not API.objects.get(name="QuoteHistoryByLegReport").active:
            connection.close()
            return Utility.json_error_response(
                code="3200", message="QuoteHistoryByLegReport Api is not active.", errors=errors
            )

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date is None or end_date is None:
            errors.append({"params": "'start_date' and 'end_date' are required."})
            return Utility.json_error_response(
                code="3201", message="QuoteHistory: Missing 'start_date' & 'end_date' parameter.", errors=errors
            )

        logs = self.get_queryset()

        try:
            rate_log_data = QuoteHistoryByLegReport().get_rate_log(
                rate_logs=logs,
                file_name=f'quote_history_by_leg_{start_date}-{end_date}.xlsx'
            )
        except ViewException as e:
            connection.close()
            errors.append({"quote_history": e.message})
            return Utility.json_error_response(code="3202", message="QuoteHistory: failed to create.", errors=errors)

        return Utility.json_response(data=rate_log_data)


class QuoteHistoryReportApi(UbbeMixin, ListAPIView):
    http_method_names = ['get']

    # Customs
    _thirty_days = 30

    def get_queryset(self):
        """
            Get initial carrier markup history queryset and apply query params to the queryset.
            :return:
        """

        if 'end_date' in self.request.query_params:
            end_date = datetime.strptime(self.request.query_params["end_date"], "%Y-%m-%d").replace(tzinfo=utc)
        else:
            end_date = datetime.now().replace(tzinfo=utc)

        if 'start_date' in self.request.query_params:
            start_date = datetime.strptime(self.request.query_params["start_date"], "%Y-%m-%d").replace(tzinfo=utc)
        else:
            start_date = end_date - timedelta(days=self._thirty_days)

        if self._sub_account.is_bbe:
            logs = RateLog.objects.select_related("sub_account__contact").filter(
                rate_date__range=[start_date, end_date]
            )
        else:
            logs = RateLog.objects.select_related("sub_account__contact").filter(
                rate_date__range=[start_date, end_date],
                sub_account=self._sub_account
            )

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            logs = logs.filter(sub_account__subaccount_number=self.request.query_params["account"])

        if 'is_no_rate' in self.request.query_params:
            logs = logs.filter(is_no_rate=self.request.query_params["is_no_rate"])

        return logs.order_by('-rate_date')

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'mode',
                openapi.IN_QUERY,
                description="Air (AI), Courier (CO), LTL (LT), FTL (FT), Sealift (SE), NA",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'account',
                openapi.IN_QUERY,
                description="Sub Account Number",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            )
        ],
        operation_id='Get Quote History All Report',
        operation_description='Get a excel sheet of quoting history.',
        responses={
            '200': 'excel sheet',
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier markup history for the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if not API.objects.get(name="QuoteHistoryAllReport").active:
            connection.close()
            return Utility.json_error_response(
                code="3200", message="QuoteHistoryByLegReport Api is not active.", errors=errors
            )

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        carrier_mode = self.request.query_params.get("mode", "NA")

        if start_date is None or end_date is None:
            errors.append({"params": "'start_time' and 'end_time' are required."})
            return Utility.json_error_response(
                code="3201", message="QuoteHistoryMode: Missing 'start_time' & 'end_time' parameter.", errors=errors
            )

        logs = self.get_queryset()

        try:
            rate_log_data = QuoteHistoryReport().get_rate_log(
                rate_logs=logs,
                file_name=f'quote_history_{start_date}-{end_date}.xlsx',
                mode=carrier_mode
            )
        except ViewException as e:
            connection.close()
            errors.append({"quote_history": e.message})
            return Utility.json_error_response(code="3202", message="QuoteHistoryMode: failed to create.", errors=errors)

        return Utility.json_response(data=rate_log_data)
