"""
    Title: Exchange Rate api views
    Description: This file will contain all functions for Exchange Rate api functions.
    Created: September 29, 2022
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
from api.models import ExchangeRate
from api.serializers_v3.private.admin.exchange_rate_serializers import PrivateExchangeRateSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ExchangeRateApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['source_currency', 'target_currency']

    # Customs
    _cache_lookup_key = "exchange_rates"

    def get_queryset(self):
        """
            Get initial exchange rates queryset and apply query params to the queryset.
            :return:
        """

        exchange_rates = cache.get(self._cache_lookup_key)

        if not exchange_rates:
            exchange_rates = ExchangeRate.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, exchange_rates, TWENTY_FOUR_HOURS_CACHE_TTL)

        return exchange_rates

    @swagger_auto_schema(
        operation_id='Get Exchange Rates',
        operation_description='Get a list of exchange rates for the system.',
        responses={
            '200': openapi.Response('Get Exchange Rates', PrivateExchangeRateSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get exchange rates for the system based on the allowed parameters and search params.
            :return:
        """

        apis = self.get_queryset()
        apis = self.filter_queryset(queryset=apis)
        serializer = PrivateExchangeRateSerializer(apis, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateExchangeRateSerializer,
        operation_id='Create Exchange Rate',
        operation_description='Create an exchange rate that could be used to convert currency.',
        responses={
            '200': openapi.Response('Create Exchange Rate', PrivateExchangeRateSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new exchange rate.
            :param request: request
            :return: Json of exchange rate.
        """
        errors = []

        json_data = request.data
        serializer = PrivateExchangeRateSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="9000", message="ExchangeRate: Invalid values.", errors=serializer.errors
            )

        try:
            exchange_rate = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="9001", message="ExchangeRate: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = exchange_rate
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class ExchangeRateDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "exchange_rates"
    _cache_lookup_key_individual = "exchange_rates_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = ExchangeRate.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"exchange_rate": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="9002", message="ExchangeRate: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Exchange Rate',
        operation_description='Get a exchange rate form the system that contains information about currency.',
        responses={
            '200': openapi.Response('Get ExchangeRate', PrivateExchangeRateSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get exchange rate information.
            :return: Json of exchange rate.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_exchange_rate = cache.get(lookup_key)

        if not cached_exchange_rate:

            try:
                api = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateExchangeRateSerializer(instance=api, many=False)
            cached_exchange_rate = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_exchange_rate, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_exchange_rate)

    @swagger_auto_schema(
        request_body=PrivateExchangeRateSerializer,
        operation_id='Update Exchange Rate',
        operation_description='Update an exchange rate currency information.',
        responses={
            '200': openapi.Response('Update Exchange Rate', PrivateExchangeRateSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update exchange rate information
            :param request: request
            :return: Json of exchange rate.
        """
        errors = []
        json_data = request.data

        try:
            exchange_rate = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateExchangeRateSerializer(exchange_rate, data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="9003", message="ExchangeRate: Invalid values.", errors=serializer.errors
            )

        try:
            exchange_rate = serializer.update(instance=exchange_rate, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="9004", message="ExchangeRate: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = exchange_rate
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Exchange Rate',
        operation_description='Delete an exchange rate.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete exchange rate from the system.
            :param request: request
            :return: Success exchange rate.
        """

        try:
            exchange_rate = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        exchange_rate.delete()

        return Utility.json_response(data={"exchange_rate": self.kwargs["pk"], "message": "Successfully Deleted"})
