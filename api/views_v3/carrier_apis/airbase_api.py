"""
    Title: Airbase Api
    Description: This file will contain all functions for airbase apis.
    Created: November 17, 2021
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
from api.models import Airbase
from api.serializers_v3.private.carriers.airbase_serializers import PrivateAirbaseSerializer, \
    PrivateCreateAirbaseSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class AirbaseApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'address__address_one', 'address__address_two', 'address__city', 'address__postal_code']

    # Customs
    _cache_lookup_key = "airbases_"

    def get_queryset(self):
        """
            Get initial airbase queryset and apply query params to the queryset.
            :return:
        """
        lookup = f'{self._cache_lookup_key}{self.request.query_params["carrier_code"]}'
        airbases = cache.get(lookup)

        if not airbases:
            airbases = Airbase.objects.select_related("carrier", "address__province__country").filter(
                carrier__code=self.request.query_params["carrier_code"]
            )

            # Store metrics for 5 hours
            cache.set(lookup, airbases, TWENTY_FOUR_HOURS_CACHE_TTL)

        return airbases

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
            )
        ],
        operation_id='Get Airbases',
        operation_description='Get a list of airbases for a carrier using the carrier code that contains address '
                              'information and the airport code that is used in multi modal.',
        responses={
            '200': openapi.Response('Get Airbases', PrivateAirbaseSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get airbases for a carrier based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"airbase": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="2100", message="Airbase: Missing 'carrier_code' parameter.", errors=errors
            )

        airbases = self.get_queryset()
        airbases = self.filter_queryset(queryset=airbases)
        serializer = PrivateAirbaseSerializer(airbases, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateAirbaseSerializer,
        operation_id='Create Airbase',
        operation_description='Create an airbases that contains address information and the airport code that is '
                              'used in multi modal.',
        responses={
            '200': openapi.Response('Create Airbase', PrivateAirbaseSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new airbase.
            :param request: request
            :return: airbase json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateAirbaseSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2101", message="Airbase: Invalid values.", errors=serializer.errors
            )

        try:
            airbase = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2102", message="Airbase: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateAirbaseSerializer(instance=airbase, many=False)
        cache.delete_pattern(f"{self._cache_lookup_key}*")

        return Utility.json_response(data=serializer.data)


class AirbaseDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "airbases_"
    _cache_lookup_key_individual = "airbase_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Airbase.objects.select_related("carrier", "address").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"airbase": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="2104", message="Airbase: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Airbase',
        operation_description='Get an airbase for a carrier that contains address information and the airport code '
                              'that is used in multi modal',
        responses={
            '200': openapi.Response('Get Airbase', PrivateAirbaseSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get airbase information.
            :return: Json of airbase.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_airbase = cache.get(lookup_key)

        if not cached_airbase:

            try:
                airbase = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateAirbaseSerializer(instance=airbase, many=False)
            cached_airbase = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_airbase, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_airbase)

    @swagger_auto_schema(
        request_body=PrivateAirbaseSerializer,
        operation_id='Update Airbase',
        operation_description='Update an airbase address information or the airport code.',
        responses={
            '200': openapi.Response('Update Airbase', PrivateAirbaseSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update airbase information
            :param request: request
            :return: Json of airbase.
        """
        errors = []
        json_data = request.data
        serializer = PrivateAirbaseSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2105", message="Airbase: Invalid values.", errors=serializer.errors
            )

        try:
            airbase = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            airbase = serializer.update(instance=airbase, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2107", message="Airbase: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = airbase
        cache.delete_pattern(f"{self._cache_lookup_key}*")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Airbase',
        operation_description='Delete an airbase for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete airbase from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            airbase = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        airbase.delete()
        cache.delete_pattern(f"{self._cache_lookup_key}*")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"airbase": self.kwargs["pk"], "message": "Successfully Deleted"})
