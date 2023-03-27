"""
    Title: Shipment Api Views V3
    Description: This file will contain all api views for shipments.
    Created: Nov 4, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Shipment
from api.serializers_v3.private.shipments.shipment_serializers import PrivateShipmentSerializer, \
    CreateShipmentSerializer
from api.serializers_v3.public.shipment_serializers import PublicShipmentSerializer
from api.utilities.utilities import Utility


class ShipmentApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'shipment_id', 'account_id', 'ff_number', 'purchase_order', 'project', 'reference_one', 'reference_two',
        'booking_number', 'username', 'origin__city', 'destination__city', 'sender__name', 'sender__company_name',
        'receiver__name', 'receiver__company_name'
    ]

    # Customs
    _thirty_days = 30
    _shipment_status_all = "0"  # Defaults to All Shipments
    _shipment_status_in_progress = "1"
    _shipment_status_delivered = "2"
    _shipment_status_canceled = "3"

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

        shipments = Shipment.objects.select_related(
            "origin__province__country", "destination__province__country", "receiver", "sender", "subaccount__contact"
        ).prefetch_related(
            "shipment_document_shipment",
        ).filter(creation_date__range=[start_date, end_date])

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            shipments = shipments.filter(subaccount__subaccount_number=self.request.query_params["account"])
        else:
            shipments = shipments.filter(subaccount=self._sub_account)

        if 'is_dangerous_good' in self.request.query_params:
            shipments = shipments.filter(is_dangerous_good=self.request.query_params["is_dangerous_good"])

        if 'username' in self.request.query_params:
            shipments = shipments.filter(username=self.request.query_params["username"])

        if 'shipment_status' in self.request.query_params:
            shipment_status = self.request.query_params.get("shipment_status")

            if shipment_status == self._shipment_status_in_progress:
                shipments = shipments.filter(is_shipped=True)
            elif shipment_status == self._shipment_status_delivered:
                shipments = shipments.filter(is_shipped=True, is_delivered=True)
            elif shipment_status == self._shipment_status_canceled:
                shipments = shipments.filter(Q(is_cancel=True) | Q(is_cancel_completed=True))
            else:
                shipments = shipments.filter(is_shipped=True)

        return shipments.order_by("-creation_date")

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PrivateShipmentSerializer
        else:
            return PublicShipmentSerializer

    @swagger_auto_schema(
        operation_id='Get Shipments',
        operation_description='Get a list of shipments with information containing origin, destination, '
                              'contact details, and references.',
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
            '200': openapi.Response('Get Shipments', PublicShipmentSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipments based on the allowed parameters and determine..
            :return:
        """

        shipments = self.get_queryset()
        shipments = self.filter_queryset(queryset=shipments)
        serializer = self.get_serializer_class()
        serializer = serializer(shipments, many=True)

        return Utility.json_response(data=serializer.data)

    def post(self, request, *args, **kwargs):
        """
            Create a new shipment.
            :param request: request
            :return: Json of promo code.
        """
        errors = []
        json_data = request.data
        serializer = CreateShipmentSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1200", message="Shipment: Invalid values.", errors=serializer.errors
            )
        try:
            serializer.validated_data["user"] = self.request.user
            shipment = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1201", message="Shipment: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = shipment

        response_serializer = self.get_serializer_class()
        response_serializer = response_serializer(serializer.instance, many=False)
        return Utility.json_response(data=response_serializer.data)


class ShipmentDetailApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        if self._sub_account.is_bbe:
            return Shipment.objects.select_related(
                "origin__province__country",
                "destination__province__country",
                "receiver",
                "sender",
                "subaccount__contact"
            ).get(shipment_id=self.kwargs["shipment_id"])
        else:
            return Shipment.objects.select_related(
                "origin__province__country",
                "destination__province__country",
                "receiver",
                "sender",
                "subaccount__contact"
            ).get(shipment_id=self.kwargs["shipment_id"], subaccount=self._sub_account)

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PrivateShipmentSerializer
        else:
            return PublicShipmentSerializer

    @swagger_auto_schema(
        operation_id='Get Shipment',
        operation_description='Get a shipment with information containing origin, destination, contact details, and '
                              'references.',
        manual_parameters=[
            openapi.Parameter(
                'shipment_id', openapi.IN_QUERY, description="ubbe Number", type=openapi.TYPE_STRING
            )
        ],
        responses={
            '200': openapi.Response('Get Shipment', PublicShipmentSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipment based on the allowed parameters and determine.
            :return:
        """
        errors = []

        try:
            shipment = self.get_queryset()
        except ObjectDoesNotExist:
            errors.append({
                "shipment": "'shipment_id' does not exist or you do not have permission to view this shipment."
            })
            return Utility.json_error_response(code="2700", message="Shipment: Not Found.", errors=errors)

        serializer = self.get_serializer_class()
        serializer = serializer(shipment, many=False)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Update Shipment',
        operation_description='Update shipment with information containing origin, destination, contact details, and '
                              'references.',
        responses={
            '200': openapi.Response('Update Shipment', PublicShipmentSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update shipment
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        serializer = self.get_serializer_class()

        try:
            shipment = self.get_queryset()
        except ObjectDoesNotExist:
            errors.append({
                "shipment": "'shipment_id' does not exist or you do not have permission to view this shipment."
            })
            return Utility.json_error_response(code="2701", message="Shipment: Not Found.", errors=errors)

        serializer = serializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2702", message="Shipment: Invalid values.", errors=serializer.errors
            )

        try:
            serializer.update(instance=shipment, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2703", message="Shipment: Failed to update.", errors=errors)

        return Utility.json_response(data=serializer.data)
