"""
    Title: Bill of Lading Apis
    Description: This file will contain all functions for bill of lading api.
    Created: November 16, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import BillOfLading
from api.serializers_v3.private.carriers.bill_of_lading_serializers import PrivateBillOfLadingSerializer, \
    PrivateCreateBillOfLadingSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class BillOfLadingApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['dispatch__location', 'bill_of_lading']

    # Customs
    _cache_lookup_key = "bill_of_ladings_"

    def get_queryset(self):
        """
            Get initial carrier service queryset and apply query params to the queryset.
            :return:
        """
        lookup = f'{self._cache_lookup_key}{self.request.query_params["carrier_code"]}'
        bill_of_ladings = cache.get(lookup)

        if not bill_of_ladings:
            bill_of_ladings = BillOfLading.objects.select_related(
                "dispatch__carrier"
            ).filter(dispatch__carrier__code=self.request.query_params["carrier_code"])

            # Store metrics for 5 hours
            cache.set(lookup, bill_of_ladings, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'dispatch_id' in self.request.query_params:
            bill_of_ladings = bill_of_ladings.filter(dispatch__id=self.request.query_params["dispatch_id"])

        if 'is_available' in self.request.query_params:
            bill_of_ladings = bill_of_ladings.filter(is_available=self.request.query_params["is_available"])

        return bill_of_ladings

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter(
            'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
        )],
        operation_id='Get Bill of Ladings',
        operation_description='Get a list of bill of ladings for a carrier using the carrier code that contains '
                              'the bill of lading number and if its available or not.',
        responses={
            '200': openapi.Response('Get Bill of Ladings', PrivateBillOfLadingSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get bill of ladings based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"bill_of_lading": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="2200", message="Bill of Lading: Missing 'carrier_code' parameter.", errors=errors
            )

        bill_of_ladings = self.get_queryset()
        bill_of_ladings = self.filter_queryset(queryset=bill_of_ladings)
        serializer = PrivateBillOfLadingSerializer(bill_of_ladings, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateBillOfLadingSerializer,
        operation_id='Create Bill of Lading',
        operation_description='Create an bill of lading with new bill of lading number and if its available.',
        responses={
            '200': openapi.Response('Create Bill of Lading', PrivateBillOfLadingSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new bill of lading.
            :param request: request
            :return: json of bill of lading.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateBillOfLadingSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2201", message="Bill of Lading: Invalid values.", errors=serializer.errors
            )

        try:
            service = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2202", message="Bill of Lading: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateBillOfLadingSerializer(instance=service, many=False)
        cache.delete_pattern(f"{self._cache_lookup_key}*")

        return Utility.json_response(data=serializer.data)


class BillOfLadingDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "bill_of_ladings_"
    _cache_lookup_key_individual = "bill_of_lading_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = BillOfLading.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"bill_of_lading": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="2204", message="Bill of Lading: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Bill of Lading',
        operation_description='Get an bill of lading for a carrier contains the bill of lading number and if its '
                              'available or not.',
        responses={
            '200': openapi.Response('Get Airbase', PrivateBillOfLadingSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get bill of lading information.
            :return: Json of bill of lading.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_bol = cache.get(lookup_key)

        if not cached_bol:

            try:
                bol = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateBillOfLadingSerializer(instance=bol, many=False)
            cached_bol = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_bol, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_bol)

    @swagger_auto_schema(
        request_body=PrivateBillOfLadingSerializer,
        operation_id='Update Bill of Lading',
        operation_description='Update an bill of lading or if its become unavailable.',
        responses={
            '200': openapi.Response('Update Bill of Lading', PrivateBillOfLadingSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update bill of lading information
            :param request: request
            :return: Json of bill of lading.
        """
        errors = []
        json_data = request.data
        serializer = PrivateBillOfLadingSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2205", message="Bill of Lading: Invalid values.", errors=serializer.errors
            )

        try:
            bol = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            bol = serializer.update(instance=bol, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2207", message="Bill of Lading: Failed to update.", errors=errors)

        serializer.instance = bol
        cache.delete_pattern(f"{self._cache_lookup_key}*")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Bill of Lading',
        operation_description='Delete an bill of lading for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete bill of lading from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            bol = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        bol.delete()
        cache.delete_pattern(f"{self._cache_lookup_key}*")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"bill_of_lading": self.kwargs["pk"], "message": "Successfully Deleted"})
