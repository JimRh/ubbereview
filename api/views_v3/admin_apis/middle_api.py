"""
    Title: Middle Location api views
    Description: This file will contain all functions for middle location api functions.
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
from api.models import MiddleLocation
from api.serializers_v3.private.admin.middle_serializers import PrivateMiddleLocationSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class MiddleLocationApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', "email", 'address__address', 'address__city', 'address__postal_code']

    # Customs
    _cache_lookup_key = "location_middle"

    def get_queryset(self):
        """
            Get initial interline middle locations queryset and apply query params to the queryset.
            :return:
        """

        locations = cache.get(self._cache_lookup_key)

        if not locations:
            locations = MiddleLocation.objects.select_related("address__province__country").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, locations, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'is_available' in self.request.query_params:
            locations = locations.filter(is_available=self.request.query_params["is_available"])

        return locations

    @swagger_auto_schema(
        operation_id='Get Middle Locations',
        operation_description='Get a list of middle locations for ubbe interline locations contains address details '
                              'and code',
        responses={
            '200': openapi.Response('Get Middle Locations', PrivateMiddleLocationSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get interline middle locations for the system based on the allowed parameters and search params.
            :return:
        """

        apis = self.get_queryset()
        apis = self.filter_queryset(queryset=apis)
        serializer = PrivateMiddleLocationSerializer(apis, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateMiddleLocationSerializer,
        operation_id='Create Middle Location',
        operation_description='Create an middle location for ubbe interline locations which contains address details '
                              'and code',
        responses={
            '200': openapi.Response('Create Middle Location', PrivateMiddleLocationSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new interline middle location.
            :param request: request
            :return: Json list of middle location.
        """
        errors = []
        json_data = request.data
        serializer = PrivateMiddleLocationSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4400", message="Middle Location: Invalid values.", errors=serializer.errors
            )

        try:
            api = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4401", message="Middle Location: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = api
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class MiddleLocationDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "location_middle"
    _cache_lookup_key_individual = "location_middle_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = MiddleLocation.objects.select_related("address__province__country").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Middle Location',
        operation_description='Get a middle location for ubbe interline locations which contains address details '
                              'and code',
        responses={
            '200': openapi.Response('Get Middle Location', PrivateMiddleLocationSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get interline middle location information.
            :return: Json of interline middle location.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_location = cache.get(lookup_key)

        if not cached_location:

            try:
                location = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateMiddleLocationSerializer(instance=location, many=False)
            cached_location = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_location, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_location)

    @swagger_auto_schema(
        request_body=PrivateMiddleLocationSerializer,
        operation_id='Update Middle Location',
        operation_description='Update a middle location address details or code',
        responses={
            '200': openapi.Response('Update Middle Location', PrivateMiddleLocationSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update interline middle location information
            :param request: request
            :return: Json of interline middle location.
        """
        errors = []
        json_data = request.data
        serializer = PrivateMiddleLocationSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4404", message="Middle Location: Invalid values.", errors=serializer.errors
            )

        try:
            location = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            location = serializer.update(instance=location, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4406", message="Middle Location: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = location
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Middle Location',
        operation_description='Delete a middle location for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete interline middle location from the system.
            :param request: request
            :return: Success message.
        """

        try:
            location = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        location.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"middle_location": self.kwargs["pk"], "message": "Successfully Deleted"})
