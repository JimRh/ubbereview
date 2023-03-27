"""
    Title: Country  Serializers
    Description: This file will contain all functions for country serializers.
    Created: November 19, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Country
from api.serializers_v3.common.country_serializer import CountrySerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class GetCountries(UbbeMixin, APIView):
    """
        Get a List of all countries, or create a new country.
    """
    http_method_names = ['get', 'post']

    # Customs
    _cache_lookup_key = "countries"
    _sub_account = None

    @swagger_auto_schema(
        operation_id='Get Countries',
        operation_description='Get all countries in ubbe.',
        responses={
            '200': openapi.Response('Countries', CountrySerializer(many=True)),
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get all countries.
            :param request: request
            :return: Json list of countries.
        """

        data = cache.get(self._cache_lookup_key)

        if not data:
            countries = Country.objects.all().order_by("name")
            serializer = CountrySerializer(countries, many=True)
            data = serializer.data

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, data, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=data)

    @swagger_auto_schema(
        request_body=CountrySerializer,
        operation_id='Create Country',
        operation_description='Create a country that contains name, code, and currency.',
        responses={
            '200': openapi.Response('Create Country', CountrySerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new country.
            :param request: request
            :return: Json of country.
        """
        errors = []
        json_data = request.data
        serializer = CountrySerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1401", message="Country: Invalid values.", errors=serializer.errors
            )

        try:
            country = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1400", message="Country: failed to save.", errors=errors)

        cache.delete(self._cache_lookup_key)
        serializer.instance = country
        return Utility.json_response(data=serializer.data)


class CountryDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "countries"
    _cache_lookup_key_individual = "countries_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Country.objects.get(code=self.kwargs["code"])
        except ObjectDoesNotExist:
            errors.append({"country": f'{self.kwargs["code"]} not found or you do not have permission.'})
            raise ViewException(code="1402", message="Country: Invalid Code.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Country',
        operation_description='Get a country that contains name, code, and currency.',
        responses={
            '200': openapi.Response('Get Country', CountrySerializer),
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get country information.
            :return:
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["code"]}'
        cached_country = cache.get(lookup_key)

        if not cached_country:

            try:
                country = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = CountrySerializer(country, many=False)
            cached_country = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_country, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_country)

    @swagger_auto_schema(
        request_body=CountrySerializer,
        operation_id='Update Country',
        operation_description='Update a country that contains name, code, and currency.',
        responses={
            '200': openapi.Response('Update Country', CountrySerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update country information
            :param request: request
            :return: Json of country.
        """
        errors = []
        json_data = request.data
        serializer = CountrySerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1405", message="Country: Invalid values.",  errors=serializer.errors
            )

        try:
            country = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            country = serializer.update(instance=country, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1404", message="Country: failed to update.", errors=errors)

        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["code"]}')
        serializer.instance = country
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Country',
        operation_description='Delete a country for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete country from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            country = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        country.province_country.all().delete()
        country.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["code"]}')

        return Utility.json_response(data={"country": self.kwargs["code"], "message": "Successfully Deleted"})
