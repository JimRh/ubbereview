"""
    Title: Shipment Api Views V3
    Description: This file will contain all api views for shipments.
    Created: Nov 4, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import Leg
from api.serializers_v3.public.search_shipment_serializer import SearchLegSerializer
from api.utilities.utilities import Utility


class FindShipmentApi(UbbeMixin, ListAPIView):
    http_method_names = ['get']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'shipment__shipment_id', 'shipment__account_id', 'shipment__ff_number', 'shipment__purchase_order',
        'shipment__project', 'shipment__reference_one', 'shipment__reference_two','shipment__booking_number',
        'shipment__quote_id', 'leg_id', 'tracking_identifier', 'carrier_pickup_identifier', 'carrier_api_id'
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

        legs = Leg.objects.select_related(
            "shipment__subaccount__contact", "carrier", "origin__province__country", "destination__province__country"
        ).filter(shipment__creation_date__range=[start_date, end_date])

        if not self._sub_account.is_bbe:
            legs = legs.filter(shipment__subaccount=self._sub_account)
        elif 'account' in self.request.query_params:
            legs = legs.filter(shipment__subaccount__subaccount_number=self.request.query_params["account"])

        if "username" in self.request.query_params:
            legs = legs.filter(shipment__username=self.request.query_params["username"])

        return legs.order_by("-shipment__creation_date")

    @swagger_auto_schema(
        operation_id='Search Shipment Legs',
        operation_description='Search shipment legs fields with a specific value',
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            )
        ],
        responses={
            '200': openapi.Response('Search Shipment Legs', SearchLegSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipments based on the allowed parameters and determine..
            :return:
        """
        legs = self.get_queryset()
        legs = self.filter_queryset(queryset=legs)
        serializer = SearchLegSerializer(legs, many=True)

        return Utility.json_response(data=serializer.data)
