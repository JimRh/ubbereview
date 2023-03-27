"""
    Title: Tracking Report apis
    Description: This file will contain functions to produce reports.
    Created: November 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta
from uuid import UUID

from django.db import connection
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.apis.reports.tracking_report import TrackingReportData
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import API, Shipment

# TODO - Should this be cached or not.
from api.utilities.utilities import Utility


class TrackingReportApi(UbbeMixin, APIView):
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
            shipments = Shipment.objects.select_related(
                "origin__province__country",
                "destination__province__country",
                "subaccount__contact"
            ).prefetch_related(
                "leg_shipment__carrier",
                "leg_shipment__origin__province__country",
                "leg_shipment__destination__province__country"
            ).filter(
                creation_date__range=[start_date, end_date]
            )
        else:
            shipments = Shipment.objects.select_related(
                "origin__province__country",
                "destination__province__country",
                "subaccount__contact"
            ).prefetch_related(
                "leg_shipment__carrier",
                "leg_shipment__origin__province__country",
                "leg_shipment__destination__province__country"
            ).filter(
                creation_date__range=[start_date, end_date],
                subaccount=self._sub_account,
            )

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            shipments = shipments.filter(subaccount__subaccount_number=self.request.query_params["account"])

        return shipments

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
        operation_id='Get Tracking Report',
        operation_description='Get a list of shipment tracking data to create a excel sheet on the other end.',
        responses={
            '200': 'List of tracking data for report',
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Tracking Report data.
            :param request: request object
            :return: Metric Data
        """
        errors = []

        if not API.objects.get(name="TrackingReport").active:
            connection.close()
            return Utility.json_error_response(code="3200", message="TrackingReport Api is not active.", errors=errors)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        account = self.request.query_params.get("account")

        if start_date is None or end_date is None:
            errors.append({"params": "'start_time' and 'end_time' are required."})
            return Utility.json_error_response(
                code="3201", message="TrackingReport: Missing 'start_time' & 'end_time' parameter.", errors=errors
            )

        if account and self._sub_account.is_bbe:
            try:
                UUID(account)
            except ValueError:
                errors.append({"params": "'account' must be UUID."})
                return Utility.json_error_response(
                    code="3202", message="TrackingReport: 'account' must be UUID.", errors=errors
                )

        shipments = self.get_queryset()

        try:
            tracking_data = TrackingReportData().get_tracking(
                shipments=shipments,
                file_name=f'tracking_{start_date}-{end_date}.xlsx'
            )
        except ViewException as e:
            errors.append({"tracking_report": e.message})
            return Utility.json_error_response(code="3203", message="TrackingReport: failed to create.", errors=errors)

        return Utility.json_response(data=tracking_data)
