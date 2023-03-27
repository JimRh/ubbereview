"""
    Title: Leg Api Views V3
    Description: This file will contain all functions for Leg Api views
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Leg
from api.serializers_v3.private.shipments.leg_serializers import PrivateLegSerializer, CreateLegSerializer
from api.serializers_v3.public.leg_serializer import PublicLegSerializer
from api.utilities.utilities import Utility


class LegApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'leg_id', 'type', 'carrier__name', 'service_code', 'origin__city', 'destination__city', 'tracking_identifier',
        'carrier_pickup_identifier', 'carrier_api_id'
    ]

    # Customs
    _thirty_days = 30
    _leg_status_all = "0"  # Defaults to All Shipments
    _leg_status_in_progress = "1"
    _leg_status_delivered = "2"
    _leg_status_canceled = "3"

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
            "shipment__subaccount__contact",
            "carrier",
            "origin__province__country",
            "destination__province__country"
        ).prefetch_related(
            "surcharge_leg",
            "shipdocument_leg",
            "tracking_status_leg"
        ).filter(ship_date__range=[start_date, end_date])

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            legs = legs.filter(shipment__subaccount__subaccount_number=self.request.query_params["account"])
        else:
            legs = legs.filter(shipment__subaccount=self._sub_account)

        if 'is_dangerous_good' in self.request.query_params:
            legs = legs.filter(is_dangerous_good=self.request.query_params["is_dangerous_good"])

        if 'username' in self.request.query_params:
            legs = legs.filter(shipment__username=self.request.query_params["username"])

        if 'shipment_status' in self.request.query_params:
            shipment_status = self.request.query_params.get("shipment_status")

            if shipment_status == self._leg_status_in_progress:
                legs = legs.filter(is_shipped=True)
            elif shipment_status == self._leg_status_delivered:
                legs = legs.filter(is_shipped=True, is_delivered=True)
            elif shipment_status == self._leg_status_canceled:
                legs = legs.filter(is_shipped=False)
            else:
                legs = legs.filter(is_shipped=True)

        return legs.order_by("-ship_date")

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PrivateLegSerializer
        else:
            return PublicLegSerializer

    @swagger_auto_schema(
        operation_id='Get Legs',
        operation_description='Get a list of shipment legs with information containing origin, destination, '
                              'carrier details.',
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_dangerous_good', openapi.IN_QUERY, description="Only DG Legs", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'shipment_status',
                openapi.IN_QUERY,
                description="All (0), In Progress (1), Delivered (2), Canceled (3)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            '200': openapi.Response('Get Legs', PublicLegSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipment legs based on the allowed parameters and determine.
            :return:
        """

        legs = self.get_queryset()
        legs = self.filter_queryset(queryset=legs)
        serializer = self.get_serializer_class()
        serializer = serializer(legs, many=True)

        return Utility.json_response(data=serializer.data)

    def post(self, request, *args, **kwargs):
        """
            Create shipment leg to be added to shipment.
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        serializer = CreateLegSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2800", message="Leg: Invalid values.", errors=serializer.errors
            )

        serializer.validated_data["shipment_id"] = json_data["shipment_id"]

        try:
            serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2801", message="Leg: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        response_serializer = self.get_serializer_class()
        response_serializer = response_serializer(serializer.instance, many=False)
        return Utility.json_response(data=response_serializer.data)

class LegDetailApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        legs = Leg.objects.select_related(
            "shipment__subaccount__contact",
            "carrier",
            "origin__province__country",
            "destination__province__country"
        ).prefetch_related(
            "surcharge_leg",
            "shipdocument_leg",
            "tracking_status_leg"
        ).filter(shipment__shipment_id=self.kwargs["shipment_id"])

        if not self._sub_account.is_bbe:
            legs = legs.filter(shipment__subaccount=self._sub_account)

        if 'leg_id' in self.request.query_params:
            legs = legs.filter(leg_id=self.request.query_params["leg_id"])

        return legs

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PrivateLegSerializer
        else:
            return PublicLegSerializer

    @swagger_auto_schema(
        operation_id='Get Shipment Legs',
        operation_description='Get shipment legs with information containing origin, destination, carrier details.',
        manual_parameters=[
            openapi.Parameter(
                'leg_id', openapi.IN_QUERY, description="Get individual leg", type=openapi.TYPE_STRING
            )
        ],
        responses={
            '200': openapi.Response('Get Shipment Legs', PublicLegSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipment legs for a shipment or individual leg based on the allowed parameters and determine.
            :return:
        """

        legs = self.get_queryset()
        serializer = self.get_serializer_class()
        serializer = serializer(legs, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=CreateLegSerializer,
        operation_id='Create Leg',
        operation_description='Create a shipment leg with information containing origin, destination, carrier details.',
        responses={
            '200': openapi.Response('Create Leg', CreateLegSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )

    def put(self, request, *args, **kwargs):
        """
            Update shipment leg details
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        serializer = self.get_serializer_class()

        if not json_data.get("leg_id"):
            errors.append({"leg": "'leg_id' is Mandatory Field."})
            return Utility.json_error_response(code="2803", message="Leg: Missing 'leg_id' parameter.", errors=errors)

        try:
            leg = Leg.objects.get(leg_id=json_data.get("leg_id", ""))
            del json_data["leg_id"]
        except ObjectDoesNotExist:
            errors.append({"leg": f'{json_data.get("leg_id")} not found or you do not have permission.'})
            return Utility.json_error_response(code="2804", message="Leg: Not Found.", errors=errors)

        serializer = serializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2805", message="Leg: Invalid values.", errors=serializer.errors
            )

        try:
            serializer.update(instance=leg, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2806", message="Leg: Failed to update.", errors=errors)

        return Utility.json_response(data=serializer.data)
