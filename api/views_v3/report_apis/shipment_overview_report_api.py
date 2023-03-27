"""
    Title: Shipment Overview Report apis
    Description: This file will contain functions to account reports.
    Created: June 16, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime

from django.db import connection
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.apis.reports.shipment_overview_report import ShipmentOverviewReportData
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import API, Shipment

from api.utilities.utilities import Utility


class ShipmentOverviewReportApi(UbbeMixin, APIView):
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

        shipments = Shipment.objects.select_related(
            "origin__province__country",
            "destination__province__country",
            "receiver",
            "sender",
            "subaccount__contact"
        ).prefetch_related(
            "leg_shipment__carrier",
            "leg_shipment__origin__province__country",
            "leg_shipment__destination__province__country",
            "package_shipment"
        ).filter(creation_date__range=[start_date, end_date], is_shipped=True)

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            shipments = shipments.filter(subaccount__subaccount_number=self.request.query_params["account"])
        elif self._sub_account.is_bbe:
            pass
        else:
            shipments = shipments.filter(subaccount=self._sub_account)

        if 'username' in self.request.query_params:
            shipments = shipments.filter(username=self.request.query_params["username"])

        return shipments

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="YYYY-mm-dd", type=openapi.TYPE_STRING, required=True
            )
        ],
        operation_id='Get Shipment Overview Report',
        operation_description='Get a list of Shipment Overview data to create a report.',
        responses={
            '200': 'Dictionary Report',
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Shipment Overview Report.
            :param request: request object
            :return: Metric Data
        """
        errors = []

        if not API.objects.get(name="ShipmentOverviewReportApi").active:
            connection.close()
            return Utility.json_error_response(code="3200", message="Shipment Overview Report Api is not active.", errors=errors)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date is None or end_date is None:
            errors.append({"params": "'start_time' and 'end_time' are required."})
            return Utility.json_error_response(
                code="3201", message="ShipmentOverviewReport: Missing 'start_date' & 'end_date' parameter.", errors=errors
            )

        shipments = self.get_queryset()

        try:
            shipment_overview_report = ShipmentOverviewReportData().get_shipment_overview(
                shipments=shipments,
                file_name=f'shipment_overview_{start_date}-{end_date}.xlsx'
            )
        except ViewException as e:
            connection.close()
            errors.append({"account": e.message})
            return Utility.json_error_response(code="3202", message="ShipmentOverviewReport: failed to create.", errors=errors)

        return Utility.json_response(data=shipment_overview_report)
