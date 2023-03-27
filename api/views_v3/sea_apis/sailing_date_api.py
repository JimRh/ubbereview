
"""
    Title: Sailing Dates api views
    Description: This file will contain all functions for sailing dates api functions.
    Created: April 21, 2022
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
from api.models import SealiftSailingDates
from api.serializers_v3.private.sea.port_serializers import PrivatePortSerializer
from api.serializers_v3.private.sea.sailing_date_serializers import PrivateSailingDateSerializer, \
    PrivateCreateSailingDateSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class SealiftSailingDatesApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'status', 'port__name', 'port__code']

    # Customs
    _cache_lookup_key = "sailing_date"

    def get_queryset(self):
        """
            Get initial ports queryset and apply query params to the queryset.
            :return:
        """

        sailings = cache.get(self._cache_lookup_key)

        if not sailings:
            sailings = SealiftSailingDates.objects.select_related("carrier", "port__address__province").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, sailings, TWENTY_FOUR_HOURS_CACHE_TTL)

        return sailings

    @swagger_auto_schema(
        operation_id='Get Sailing',
        operation_description='Get a list of Sailings which includes sailing dates, cutoffs, and port destinations.',
        responses={
            '200': openapi.Response('Get Sailing', PrivateSailingDateSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get webhooks for the system based on the allowed parameters and search params.
            :return:
        """

        sailings = self.get_queryset()
        sailings = self.filter_queryset(queryset=sailings)
        serializer = PrivateSailingDateSerializer(sailings, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateSailingDateSerializer,
        operation_id='Create Sailing',
        operation_description='Create a sailing date which includes sailing dates, cutoffs, and port destinations.',
        responses={
            '200': openapi.Response('Create Sailing', PrivateCreateSailingDateSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new port.
            :param request: request
            :return: Json of port.
        """
        errors = []
        serializer = PrivateCreateSailingDateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="8000", message="Sailing: Invalid values.", errors=serializer.errors
            )

        try:
            sailing = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="8001", message="Sailing: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateSailingDateSerializer(instance=sailing, many=False)
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class SailingDateDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "sailing_date"
    _cache_lookup_key_individual = "sailing_date_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = SealiftSailingDates.objects.select_related(
                "carrier", "port__address__province"
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"sailing": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="8003", message="Sailing: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Sailing Date',
        operation_description='Get a sailing Date which includes sailing dates, cutoffs, and port destinations.',
        responses={
            '200': openapi.Response('Get Sailing Date', PrivateSailingDateSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Sailing Date information.
            :return: Json of Sailing Date.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_sailing = cache.get(lookup_key)

        if not cached_sailing:

            try:
                sailing = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateSailingDateSerializer(instance=sailing, many=False)
            cached_sailing = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_sailing, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_sailing)

    @swagger_auto_schema(
        request_body=PrivatePortSerializer,
        operation_id='Update Sailing Date',
        operation_description='Update a port which includes address information and port code.',
        responses={
            '200': openapi.Response('Update Port', PrivateSailingDateSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Sailing Date information
            :param request: request
            :return: Json of Sailing Date.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateSailingDateSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="8004", message="Sailing: Invalid values.", errors=serializer.errors
            )

        try:
            sailing = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            sailing = serializer.update(instance=sailing, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="8005", message="Sailing: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateSailingDateSerializer(instance=sailing, many=False)
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Sailing Date',
        operation_description='Delete a Sailing Date.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete Sailing Date from the system.
            :param request: request
            :return: Success message.
        """

        try:
            sailing = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        sailing.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"sailing_date": self.kwargs["pk"], "message": "Successfully Deleted"})
