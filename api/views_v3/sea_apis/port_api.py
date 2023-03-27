"""
    Title: Port api views
    Description: This file will contain all functions for port api functions.
    Created: November 23, 2021
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
from api.models import Port
from api.serializers_v3.private.sea.port_serializers import PrivatePortSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class PortApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'address__address', 'address__city', 'address__postal_code']

    # Customs
    _cache_lookup_key = "ports"

    def get_queryset(self):
        """
            Get initial ports queryset and apply query params to the queryset.
            :return:
        """

        ports = cache.get(self._cache_lookup_key)

        if not ports:
            ports = Port.objects.select_related("address__province__country").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, ports, TWENTY_FOUR_HOURS_CACHE_TTL)

        return ports

    @swagger_auto_schema(
        operation_id='Get Ports',
        operation_description='Get a list of ports which includes address information and port code.',
        responses={
            '200': openapi.Response('Get Ports', PrivatePortSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get webhooks for the system based on the allowed parameters and search params.
            :return:
        """

        ports = self.get_queryset()
        ports = self.filter_queryset(queryset=ports)
        serializer = PrivatePortSerializer(ports, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivatePortSerializer,
        operation_id='Create Port',
        operation_description='Create a port which includes address information and port code.',
        responses={
            '200': openapi.Response('Create Port', PrivatePortSerializer),
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
        json_data = request.data
        serializer = PrivatePortSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4600", message="Port: Invalid values.", errors=serializer.errors
            )

        try:
            port = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4601", message="Port: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = port
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class PortDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "ports"
    _cache_lookup_key_individual = "ports_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Port.objects.select_related("address__province__country").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"port": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4603", message="Port: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Port',
        operation_description='Get a port which includes address information and port code',
        responses={
            '200': openapi.Response('Get Port', PrivatePortSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get port information.
            :return: Json of port.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_port = cache.get(lookup_key)

        if not cached_port:

            try:
                port = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivatePortSerializer(instance=port, many=False)
            cached_port = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_port, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_port)

    @swagger_auto_schema(
        request_body=PrivatePortSerializer,
        operation_id='Update Port',
        operation_description='Update a port which includes address information and port code.',
        responses={
            '200': openapi.Response('Update Port', PrivatePortSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update port information
            :param request: request
            :return: Json of port.
        """
        errors = []
        json_data = request.data
        serializer = PrivatePortSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4604", message="Port: Invalid values.", errors=serializer.errors
            )

        try:
            port = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            port = serializer.update(instance=port, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4606", message="Port: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = port
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete port',
        operation_description='Delete a port.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete port from the system.
            :param request: request
            :return: Success message.
        """

        try:
            port = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        port.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"port": self.kwargs["pk"], "message": "Successfully Deleted"})
