"""
    Title: Account Report apis
    Description: This file will contain functions to account reports.
    Created: June 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.db import connection
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.apis.reports.account_report import AccountReport
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import API, SubAccount

from api.utilities.utilities import Utility


class AccountReportApi(UbbeMixin, APIView):
    http_method_names = ['get']

    # Customs
    _thirty_days = 30

    def get_queryset(self):
        """
            Get initial carrier markup history queryset and apply query params to the queryset.
            :return:
        """
        start_date = datetime.strptime(self.request.query_params["start_date"], "%Y-%m-%d").replace(tzinfo=utc)
        end_date = datetime.strptime(self.request.query_params["end_date"], "%Y-%m-%d").replace(tzinfo=utc)

        accounts = SubAccount.objects.select_related(
            "contact",
            "address__province__country",
            "tier",
            "markup"
        ).filter(creation_date__range=[start_date, end_date])

        return accounts

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            )
        ],
        operation_id='Get Account Report',
        operation_description='Get a list of account data to create a report.',
        responses={
            '200': 'Dictionary Report',
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Account Report.
            :param request: request object
            :return: Metric Data
        """
        errors = []

        if not API.objects.get(name="AccountReportApi").active:
            connection.close()
            return Utility.json_error_response(code="3200", message="Account Report Api is not active.", errors=errors)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date is None or end_date is None:
            errors.append({"params": "'start_time' and 'end_time' are required."})
            return Utility.json_error_response(
                code="3201", message="TrackingReport: Missing 'start_date' & 'end_date' parameter.", errors=errors
            )

        accounts = self.get_queryset()

        try:
            account_report = AccountReport().get_rate_log(
                accounts=accounts,
                file_name=f'accounts_{start_date}-{end_date}.xlsx'
            )
        except ViewException as e:
            connection.close()
            errors.append({"account": e.message})
            return Utility.json_error_response(code="3202", message="AccountReport: failed to create.", errors=errors)

        return Utility.json_response(data=account_report)
