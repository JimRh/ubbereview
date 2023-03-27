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
from rest_framework.views import APIView

from api.apis.google.route_apis.distance_api import GoogleDistanceApi
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import LocationDistance
from api.serializers_v3.private.admin.distance_serializers import PrivateLocationDistanceSerializer, \
    CheckLocationDistanceSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class LocationDistanceApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['origin_city', "destination_city"]

    # Customs
    _cache_lookup_key = "location_distance"

    def get_queryset(self):
        """
            Get initial location distances queryset and apply query params to the queryset.
            :return:
        """
        locations = cache.get(self._cache_lookup_key)

        if not locations:
            locations = LocationDistance.objects.select_related(
                "origin_province__country",
                "destination_province__country"
            ).all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, locations, TWENTY_FOUR_HOURS_CACHE_TTL)

        return locations

    @swagger_auto_schema(
        operation_id='Get Location Distances',
        operation_description='Get a list of location distances which contains the distance in km between two '
                              'locations and how long the estimate duration is in seconds.',
        responses={
            '200': openapi.Response('Get Location Distances', PrivateLocationDistanceSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get location distances for the system based on the allowed parameters and search params.
            :return:
        """

        apis = self.get_queryset()
        apis = self.filter_queryset(queryset=apis)
        serializer = PrivateLocationDistanceSerializer(apis, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateLocationDistanceSerializer,
        operation_id='Create Location Distance',
        operation_description='Create a location distance which contains the distance in km between two locations and '
                              'how long the estimate duration is in seconds.',
        responses={
            '200': openapi.Response('Create Location Distance', PrivateLocationDistanceSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new location distance.
            :param request: request
            :return: Json of location distance.
        """
        errors = []
        json_data = request.data
        serializer = PrivateLocationDistanceSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4300", message="Location Distance: Invalid values.", errors=serializer.errors
            )

        try:
            api = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4301", message="Location Distance: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = api
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class LocationDistanceDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "location_distance"
    _cache_lookup_key_individual = "location_distance_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = LocationDistance.objects.select_related(
                "origin_province__country",
                "destination_province__country"
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Location Distance',
        operation_description='Get a location distance which contains the distance in km between two '
                              'locations and how long the estimate duration is in seconds.',
        responses={
            '200': openapi.Response('Get Location Distance', PrivateLocationDistanceSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get location distance information.
            :return: Json of location distance
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_location = cache.get(lookup_key)

        if not cached_location:

            try:
                location = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateLocationDistanceSerializer(instance=location, many=False)
            cached_location = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_location, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_location)

    @swagger_auto_schema(
        request_body=PrivateLocationDistanceSerializer,
        operation_id='Update Location Distance',
        operation_description='Update a Location Distance contain distance and duration.',
        responses={
            '200': openapi.Response('Update Airbase', PrivateLocationDistanceSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update location distance information
            :param request: request
            :return: Json of location distance.
        """
        errors = []
        json_data = request.data
        serializer = PrivateLocationDistanceSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4304", message="Location Distance: Invalid values.", errors=serializer.errors
            )

        try:
            location = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            location = serializer.update(instance=location, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4306", message="LocationDistance Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = location
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Location Distance',
        operation_description='Delete an Location Distance for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete location distance from the system.
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

        return Utility.json_response(data={"location_distance": self.kwargs["pk"], "message": "Successfully Deleted"})


class LocationDistanceBetweenApi(UbbeMixin, APIView):
    """
        Get a Location Distance.
    """
    http_method_names = ['get', 'put', 'delete']

    @swagger_auto_schema(
        operation_id='Get Location Distance',
        operation_description='Get a location distance which contains the distance in km between two '
                              'locations and how long the estimate duration is in seconds.',
        responses={
            '200': openapi.Response('Get Location Distance', PrivateLocationDistanceSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get a Location Distance
            :param request: request
            :return: Json of Location Distance
        """
        errors = []
        data = self.request.query_params.dict()

        serializer = CheckLocationDistanceSerializer(data=data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4309", message="Location Distance: Invalid values.", errors=serializer.errors
            )

        o_city = serializer.validated_data["origin_city"]
        o_province = serializer.validated_data["origin_province"]["code"].upper()
        o_country = serializer.validated_data["origin_province"]["country"]["code"].upper()
        d_city = serializer.validated_data["destination_city"]
        d_province = serializer.validated_data["destination_province"]["code"].upper()
        d_country = serializer.validated_data["destination_province"]["country"]["code"].upper()

        lookup_key = f'distance_{o_city}_{o_province}_{o_country}_{d_city}_{d_province}_{d_country}'
        cached_distance = cache.get(lookup_key)

        if not cached_distance:
            try:
                location = GoogleDistanceApi().get_distance(
                    origin={"city": o_city, "province": o_province, "country": o_country},
                    destination={"city": d_city, "province": d_province, "country": d_country}
                )
            except ViewException as e:
                errors.append({"distance_api": e.message})
                return Utility.json_error_response(code="4310", message="Distance Api: Failed to get.", errors=errors)

            serializer.instance = location
            cached_distance = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_distance, FIVE_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_distance)
