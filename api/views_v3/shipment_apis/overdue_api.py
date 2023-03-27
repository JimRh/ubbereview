"""
    Title: Tracking Api views
    Description: This file will contain all functions for Tracking Api views
    Created: Jan 11, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.mixins.view_mixins import UbbeMixin
from api.models import Leg
from api.serializers_v3.temp_overdue import LegOverdueSerializer
from api.utilities.utilities import Utility


class LegOverdueApi(UbbeMixin, APIView):
    """
        Get a list of all legs that are overdue for pickup or delivery.
    """

    @swagger_auto_schema(
        operation_id='Get Overdue Legs',
        operation_description='Get a list of all legs that are overdue for pickup or delivery.',
        manual_parameters=[
            openapi.Parameter(
                'is_pickup_overdue',
                openapi.IN_QUERY,
                description="Only Overdue pickup shipments",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_overdue', openapi.IN_QUERY, description="Only Overdue delivery shipments", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'username', openapi.IN_QUERY, description="Filter by username", type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            '200': openapi.Response('Get Overdue Legs', LegOverdueSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get a list of all legs that are overdue for pickup or delivery.
            :param request: request
            :return: Json list of legs.
        """
        errors = []

        is_pickup_overdue = self.request.GET.get("is_pickup_overdue", "False") == "True"
        is_overdue = self.request.GET.get("is_overdue", "False") == "True"

        if is_pickup_overdue and is_overdue:
            errors.append({"params": f"Only one of 'is_pickup_overdue' or 'is_overdue' is allowed."})
            return Utility.json_error_response(
                code="6500", message="Overdue: Only one parameter allowed.", errors=errors
            )

        if is_pickup_overdue:
            overdue_legs = Leg.objects.select_related(
                "carrier",
                "origin__province__country",
                "destination__province__country",
                "shipment__subaccount__contact"
            ).filter(is_pickup_overdue=True, is_shipped=True)
        elif is_overdue:
            overdue_legs = Leg.objects.select_related(
                "carrier",
                "origin__province__country",
                "destination__province__country",
                "shipment__subaccount__contact"
            ).filter(is_overdue=True, is_shipped=True)
        else:
            overdue_legs = Leg.objects.select_related(
                "carrier",
                "origin__province__country",
                "destination__province__country",
                "shipment__subaccount__contact"
            ).filter(Q(is_pickup_overdue=True) | Q(is_overdue=True), is_shipped=True)

        if 'username' in self.request.query_params:
            overdue_legs = overdue_legs.filter(shipment__username=self.request.query_params["username"])

        if 'account' in self.request.query_params:
            overdue_legs = overdue_legs.filter(shipment__subaccount__subaccount_number=self.request.query_params["account"])

        serializer = LegOverdueSerializer(overdue_legs, many=True)
        return Utility.json_response(data=serializer.data)
