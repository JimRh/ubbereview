"""
    Title: 5T Transit Time Api
    Description: This file will contain all functions for 5T Transit Tim apis.
    Created: December 02, 2021
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
from api.models import TransitTime
from api.serializers_v3.private.cn.transit_time_serializers import PrivateTransitTimeSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CNTransitTimeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['origin', 'destination', 'rate_priority_id', 'rate_priority_code']

    # Customs
    _cache_lookup_key = "cn_transit_time"

    def get_queryset(self):
        """
            Get initial 5t transit times queryset and apply query params to the queryset.
            :return:
        """

        times = cache.get(self._cache_lookup_key)

        if not times:
            times = TransitTime.objects.all().order_by("rate_priority_code", "origin")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, times, TWENTY_FOUR_HOURS_CACHE_TTL)

        return times

    @swagger_auto_schema(
        operation_id='Get CN Transit Times',
        operation_description='Get a list of canadian north transit times for a lane and route.',
        responses={
            '200': openapi.Response('Get CN Transit Time', PrivateTransitTimeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get transit times for a carrier based on the allowed parameters and search params.
            :return:
        """

        times = self.get_queryset()
        times = self.filter_queryset(queryset=times)
        serializer = PrivateTransitTimeSerializer(times, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateTransitTimeSerializer,
        operation_id='Create CN Transit Time',
        operation_description='Create a canadian north transit times for a lane and route.',
        responses={
            '200': openapi.Response('Create CN Transit Time', PrivateTransitTimeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new transit time.
            :param request: request
            :return: transit time json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateTransitTimeSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="5900", message="CN Transit Time: Invalid values.", errors=serializer.errors
            )

        try:
            time = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="5901", message="CN Transit Time: Failed to save.", errors=errors)
        except ViewException as e:
            errors.append({"cn_transit_time": e.message})
            return Utility.json_error_response(code="5902", message="CN Transit Time: Failed to save.", errors=errors)

        serializer.instance = time
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class CNTransitTimeDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "cn_transit_time"
    _cache_lookup_key_individual = "cn_transit_time_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = TransitTime.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"cn_transit_time": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="5903", message="CN Transit Time: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get CN Transit Time',
        operation_description='Get a canadian north transit time for a lane and route.',
        responses={
            '200': openapi.Response('Get CN Transit Time', PrivateTransitTimeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get transit time information.
            :return: Json of transit time.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_time = cache.get(lookup_key)

        if not cached_time:

            try:
                time = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateTransitTimeSerializer(instance=time, many=False)
            cached_time = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_time, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_time)

    @swagger_auto_schema(
        request_body=PrivateTransitTimeSerializer,
        operation_id='Update CN Transit Time',
        operation_description='Update a canadian north transit time for a lane and route.',
        responses={
            '200': openapi.Response('Update CN Transit Time', PrivateTransitTimeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update transit time information
            :param request: request
            :return: Json of transit time.
        """
        errors = []
        json_data = request.data
        serializer = PrivateTransitTimeSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="5904", message="CN Transit Time: Invalid values.", errors=serializer.errors
            )

        try:
            time = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            time = serializer.update(instance=time, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="5906", message="CN Transit Time: Failed to update.", errors=errors)
        except ViewException as e:
            errors.append({"cn_account": e.message})
            return Utility.json_error_response(code="5907", message="CN Transit Time: Failed to update.", errors=errors)

        serializer.instance = time
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete CN Transit Time',
        operation_description='Delete an cn transit time for a lane.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete transit time from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            time = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        time.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"cn_transit_time": self.kwargs["pk"], "message": "Successfully Deleted"})
