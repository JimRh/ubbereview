"""
    Title: Dispatch Api
    Description: This file will contain all functions for dispatch apis.
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
from api.models import Dispatch
from api.serializers_v3.private.carriers.dispatch_serializer import PrivateDispatchSerializer, \
    PrivateCreateDispatchSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class DispatchApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['contact__name', 'contact__company_name', 'contact__phone', 'contact__email']

    # Customs
    _cache_lookup_key = "dispatches_"

    def get_queryset(self):
        """
            Get initial dispatch queryset and apply query params to the queryset.
            :return:
        """

        lookup = f'{self._cache_lookup_key}{self.request.query_params["carrier_code"]}'
        dispatches = cache.get(lookup)

        if not dispatches:
            dispatches = Dispatch.objects.select_related("carrier", "contact").filter(
                carrier__code=self.request.query_params["carrier_code"]
            )

            # Store metrics for 5 hours
            cache.set(lookup, dispatches, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'is_default' in self.request.query_params:
            dispatches = dispatches.filter(is_default=self.request.query_params["is_default"])

        return dispatches

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
            )
        ],
        operation_id='Get Dispatches',
        operation_description='Get a list of dispatches for a carrier using the carrier code which contains '
                              'information about the address and location, and the dispatch email to use.',
        responses={
            '200': openapi.Response('Get Dispatches', PrivateDispatchSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dispatches based on the allowed parameters and search paramms.
            :return:
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"dispatch": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="1900", message="Dispatch: Missing 'carrier_code' parameter.", errors=errors
            )

        dispatches = self.get_queryset()
        dispatches = self.filter_queryset(queryset=dispatches)
        serializer = PrivateDispatchSerializer(dispatches, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateDispatchSerializer,
        operation_id='Create Dispatch',
        operation_description='Create an dispatch with information about the address and location, and the dispatch '
                              'email to use.',
        responses={
            '200': openapi.Response('Create Dispatch', PrivateDispatchSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new dispatch.
            :param request: request
            :return: json of dispatch.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateDispatchSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1901", message="Dispatch: Invalid values.", errors=serializer.errors
            )

        try:
            dispatch = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1902", message="Dispatch: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateDispatchSerializer(instance=dispatch, many=False)
        cache.delete(f"{self._cache_lookup_key}{dispatch.carrier.code}")

        return Utility.json_response(data=serializer.data)


class DispatchDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "dispatches_"
    _cache_lookup_key_individual = "dispatch_"
    _sub_account = None

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Dispatch.objects.select_related("carrier", "contact").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"dispatch": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1904", message="Dispatch: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Dispatch',
        operation_description='Get a dispatch for a carrier using the carrier code which contains information about '
                              'the address and location, and the dispatch email to use.',
        responses={
            '200': openapi.Response('Get Dispatch', PrivateDispatchSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dispatch information.
            :return: Json of dispatch.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_dispatch = cache.get(lookup_key)

        if not cached_dispatch:

            try:
                dispatch = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateDispatchSerializer(instance=dispatch, many=False)
            cached_dispatch = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_dispatch, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_dispatch)

    @swagger_auto_schema(
        request_body=PrivateDispatchSerializer,
        operation_id='Update Dispatch',
        operation_description='Update an dispatch with information about the address and location, and the dispatch '
                              'email to use',
        responses={
            '200': openapi.Response('Update Dispatch', PrivateDispatchSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update dispatch information
            :param request: request
            :return: Json of dispatch.
        """
        errors = []
        json_data = request.data
        serializer = PrivateDispatchSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1905", message="Dispatch: Invalid values.", errors=serializer.errors
            )

        try:
            dispatch = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            dispatch = serializer.update(instance=dispatch, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1907", message="Dispatch: failed to update.", errors=errors)

        serializer.instance = dispatch
        cache.delete(f"{self._cache_lookup_key}{dispatch.carrier.code}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Dispatch',
        operation_description='Delete an dispatch for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete dispatch from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            dispatch = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f"{self._cache_lookup_key}{dispatch.carrier.code}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        dispatch.delete()

        return Utility.json_response(data={"dispatch": self.kwargs["pk"], "message": "Successfully Deleted"})
