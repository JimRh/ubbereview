"""
    Title: Carrier Service Apis
    Description: This file will contain all functions for Carrier Service Apis.
    Created: November 15, 2021
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
from api.models import CarrierService
from api.serializers_v3.common.carrier_service_serializer import CarrierServiceSerializer
from api.serializers_v3.private.carriers.create_carrier_service_serializer import PrivateCreateCarrierServiceSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CarrierServiceApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['carrier__name', 'carrier__code', 'name', 'code', 'description']

    # Customs
    _cache_rate_carrier_service_ = "rate_carrier_service_"
    _cache_lookup_key = "carrier_services_"

    def get_queryset(self):
        """
            Get initial carrier service queryset and apply query params to the queryset.
            :return:
        """

        lookup = f'{self._cache_lookup_key}{self.request.query_params["carrier_code"]}'
        services = cache.get(lookup)

        if not services:
            services = CarrierService.objects.select_related("carrier").filter(
                carrier__code=self.request.query_params["carrier_code"]
            )

            # Store metrics for 5 hours
            cache.set(lookup, services, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'is_international' in self.request.query_params:
            services = services.filter(is_international=self.request.query_params["is_international"])

        return services

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        return CarrierServiceSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
            ),
            openapi.Parameter(
                'is_international', openapi.IN_QUERY, description="International services.", type=openapi.TYPE_BOOLEAN
            )
        ],
        operation_id='Get Carrier Services',
        operation_description='Get a list of carrier services which includes information about name of the service, '
                              'description, transit time, exceptions, and if its international or not.',
        responses={
            '200': openapi.Response('Get Carrier Services', CarrierServiceSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier service levels based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"carrier_service": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="1800", message="Carrier Service: Missing 'carrier_code' parameter.", errors=errors
            )

        carriers = self.get_queryset()
        carriers = self.filter_queryset(queryset=carriers)
        serializer = self.get_serializer_class()
        serializer = serializer(carriers, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateCarrierServiceSerializer,
        operation_id='Create Carrier Service',
        operation_description='Create a carrier service which includes information about name of the service, '
                              'description, transit time, exceptions, and if its international or not.',
        responses={
            '200': openapi.Response('Create Carrier Service', CarrierServiceSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new Carrier Service.
            :param request: request
            :return: Carrier Service json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateCarrierServiceSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1801", message="Carrier Service: Invalid values.", errors=serializer.errors
            )

        try:
            service = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1802", message="Carrier Service: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f'{self._cache_lookup_key}{service.carrier.code}')
        cache.delete_pattern(f'{self._cache_rate_carrier_service_}*')

        serializer = CarrierServiceSerializer(instance=service, many=False)

        return Utility.json_response(data=serializer.data)


class CarrierServiceDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "carrier_services_"
    _cache_lookup_key_individual = "carrier_service_"
    _cache_rate_carrier_service_ = "rate_carrier_service_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = CarrierService.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"carrier_service": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1804", message="Carrier Service: not found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Carrier Service',
        operation_description='Get carrier services which includes information about name of the service, '
                              'description, transit time, exceptions, and if its international or not.',
        responses={
            '200': openapi.Response('Get Carrier Service', CarrierServiceSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier service information.
            :return: Json of carrier.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_service = cache.get(lookup_key)

        if not cached_service:

            try:
                service = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = CarrierServiceSerializer(instance=service, many=False)
            cached_service = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_service, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_service)

    @swagger_auto_schema(
        request_body=CarrierServiceSerializer,
        operation_id='Update Carrier Service',
        operation_description='Update a carrier service which includes information about name of the service, '
                              'description, transit time, exceptions, and if its international or not.',
        responses={
            '200': openapi.Response('Update Carrier Service', CarrierServiceSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update carrier service information
            :param request: request
            :return: Json of carrier service.
        """
        errors = []
        json_data = request.data
        serializer = CarrierServiceSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1805", message="Carrier Service: Invalid values.", errors=serializer.errors
            )

        try:
            service = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            service = serializer.update(instance=service, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1807", message="Carrier Service: Failed to update.", errors=errors)

        serializer.instance = service
        cache.delete(f'{self._cache_lookup_key}{service.carrier.code}')
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        cache.delete_pattern(f'{self._cache_rate_carrier_service_}*')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Carrier Service',
        operation_description='Delete a carrier service for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete carrier service from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            service = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f'{self._cache_lookup_key}{service.carrier.code}')
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        cache.delete_pattern(f'{self._cache_rate_carrier_service_}*')
        service.delete()

        return Utility.json_response(data={"carrier_service": self.kwargs["pk"], "message": "Successfully Deleted"})
