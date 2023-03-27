"""
    Title: Surcharge Api Views V3
    Description: This file will contain all functions for Surcharge Api views
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import Surcharge
from api.serializers_v3.common.surcharge_serializer import SurchargeSerializer
from api.utilities.utilities import Utility


class SurchargeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'leg__leg_id', 'leg__shipment__shipment_id', 'name'
    ]

    # Customs
    _thirty_days = 30

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
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

        surcharges = Surcharge.objects.select_related(
            "leg__shipment__subaccount",
        ).filter(leg__ship_date__range=[start_date, end_date])

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            surcharges = surcharges.filter(
                leg__shipment__subaccount__subaccount_number=self.request.query_params["account"]
            )
        else:
            surcharges = surcharges.filter(leg__shipment__subaccount=self._sub_account)

        return surcharges

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        return SurchargeSerializer

    @swagger_auto_schema(
        operation_id='Get Surcharges',
        operation_description='Get a list of surcharges charged in the system.',
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
        ],
        responses={
            '200': openapi.Response('Get Surcharges', SurchargeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get leg surchages based on the allowed parameters and determine..
            :return:
        """

        packages = self.get_queryset()
        packages = self.filter_queryset(queryset=packages)
        serializer = self.get_serializer_class()
        serializer = serializer(packages, many=True)

        return Utility.json_response(data=serializer.data)


class SurchargeDetailApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """
        surcharges = Surcharge.objects.select_related(
             "leg__shipment__subaccount",
        ).filter(leg__leg_id=self.kwargs["leg_id"])

        if not self._sub_account.is_bbe:
            surcharges = surcharges.filter(leg__shipment__subaccount=self._sub_account)

        return surcharges

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        return SurchargeSerializer

    @swagger_auto_schema(
        operation_id='Get Leg Surcharges',
        operation_description='Get a list of surcharges charged on a leg.',
        responses={
            '200': openapi.Response('Get Leg Surcharges', SurchargeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get leg surcharges for a shipment or individual leg surcharges based on the allowed parameters and determine
            :return:
        """

        surcharges = self.get_queryset()
        serializer = self.get_serializer_class()
        serializer = serializer(surcharges, many=True)

        return Utility.json_response(data=serializer.data)
