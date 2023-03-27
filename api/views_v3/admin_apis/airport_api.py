"""
    Title: Airport api views
    Description: This file will contain all functions for airport api functions.
    Created: November 22, 2021
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
from api.models import Airport
from api.serializers_v3.private.admin.airport_seralizers import PrivateAirportSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class AirportApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'address__address', 'address__city', 'address__postal_code']

    # Customs
    _cache_lookup_key = "airports"

    def get_queryset(self):
        """
            Get initial airports queryset and apply query params to the queryset.
            :return:
        """

        airports = cache.get(self._cache_lookup_key)

        if not airports:
            airports = Airport.objects.select_related("address__province__country").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, airports, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'province' in self.request.query_params:
            airports = airports.filter(address__province__code=self.request.query_params["province"])

        if 'country' in self.request.query_params:
            airports = airports.filter(address__province__country__code=self.request.query_params["country"])

        return airports

    @swagger_auto_schema(
        operation_id='Get Airports',
        operation_description='Get a list of airports that contains address information, airport code, and name.',
        responses={
            '200': openapi.Response('Get Airports', PrivateAirportSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get airports for the system based on the allowed parameters and search params.
            :return:
        """

        airports = self.get_queryset()
        airports = self.filter_queryset(queryset=airports)
        serializer = PrivateAirportSerializer(airports, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateAirportSerializer,
        operation_id='Create Airport',
        operation_description='Create an airbases that contains address information and the airport code that is '
                              'used in multi modal.',
        responses={
            '200': openapi.Response('Create Airport', PrivateAirportSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new airport.
            :param request: request
            :return: Json list of airport.
        """
        errors = []

        json_data = request.data
        serializer = PrivateAirportSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4200", message="Airport: Invalid values.", errors=serializer.errors
            )

        try:
            airport = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4201", message="Airport: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = airport
        cache.delete(self._cache_lookup_key)
        return Utility.json_response(data=serializer.data)


class AirportDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "airports"
    _cache_lookup_key_individual = "airports_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Airport.objects.select_related("address__province__country").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Airport',
        operation_description='Get an airport from the system that contains address information, airport code, '
                              'and name.',
        responses={
            '200': openapi.Response('Get Airport', PrivateAirportSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get airport information.
            :return: Json of airport.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_airports = cache.get(lookup_key)

        if not cached_airports:

            try:
                airport = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateAirportSerializer(instance=airport, many=False)
            cached_airports = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_airports, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_airports)

    @swagger_auto_schema(
        request_body=PrivateAirportSerializer,
        operation_id='Update Airport',
        operation_description='Update an airport address information, airport code, or name. ',
        responses={
            '200': openapi.Response('Update Airport', PrivateAirportSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update airport information
            :param request: request
            :return: Json of airport.
        """
        errors = []
        json_data = request.data
        serializer = PrivateAirportSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4204", message="Airport: Invalid values.", errors=serializer.errors
            )

        try:
            airport = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            airport = serializer.update(instance=airport, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4206", message="Airport: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = airport
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Airport',
        operation_description='Delete an airport from the system.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete airport from the system.
            :param request: request
            :return: Success airport.
        """

        try:
            airport = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        airport.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        return Utility.json_response(data={"airport": self.kwargs["pk"], "message": "Successfully Deleted"})
