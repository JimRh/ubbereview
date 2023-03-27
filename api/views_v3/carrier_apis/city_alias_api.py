"""
    Title: City Alias Apis
    Description: This file will contain all functions for city alias api.
    Created: November 16, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from openpyxl import load_workbook
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from api.apis.uploads.city_alias_upload import CityAliasUpload
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import CityNameAlias
from api.serializers_v3.private.carriers.city_alias_serializers import PrivateCityAliasSerializer, \
    PrivateCreateCityAliasSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CityNameAliasApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['carrier__code', 'name', 'alias']

    # Customs
    _cache_lookup_key = "aliases_"

    def get_queryset(self):
        """
            Get initial city aliases queryset and apply query params to the queryset.
            :return:
        """

        lookup = f'{self._cache_lookup_key}{self.request.query_params["carrier_code"]}'
        aliases = cache.get(lookup)

        if not aliases:
            aliases = CityNameAlias.objects.select_related("province__country").filter(
                carrier__code=self.request.query_params["carrier_code"]
            )

            # Store metrics for 5 hours
            cache.set(lookup, aliases, TWENTY_FOUR_HOURS_CACHE_TTL)

        return aliases

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
            ),
        ],
        operation_id='Get City Aliases',
        operation_description='Get a list of city aliases for a carrier which includes city and its variates.',
        responses={
            '200': openapi.Response('Get City Aliases', PrivateCityAliasSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get city aliases based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"city_alias": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="2000", message="City Alias: Missing 'carrier_code' parameter.", errors=errors
            )

        aliases = self.get_queryset()
        aliases = self.filter_queryset(queryset=aliases)
        serializer = PrivateCityAliasSerializer(aliases, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateCityAliasSerializer,
        operation_id='Create City Alias',
        operation_description='Create a city alias for a carrier which includes city and a variate.',
        responses={
            '200': openapi.Response('Create City Alias', PrivateCityAliasSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new city alias for a carrier.
            :param request: request
            :return: json of city alias.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateCityAliasSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2001", message="City Alias: Invalid values.", errors=serializer.errors
            )

        try:
            alias = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2002", message="City Alias: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateCityAliasSerializer(instance=alias, many=False)
        cache.delete(f'{self._cache_lookup_key}{alias.carrier.code}')

        return Utility.json_response(data=serializer.data)


class CityNameAliasDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "aliases_"
    _cache_lookup_key_individual = "alias_"
    _sub_account = None

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = CityNameAlias.objects.select_related("province__country").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"city_alias": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="2004", message="City Alias: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get City Alias',
        operation_description='Get a city alias for a carrier which includes city and its alias.',
        responses={
            '200': openapi.Response('Get City Alias', PrivateCityAliasSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get city alias information.
            :return: Json of city alias.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_alias = cache.get(lookup_key)

        if not cached_alias:

            try:
                alias = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateCityAliasSerializer(instance=alias, many=False)
            cached_alias = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_alias, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_alias)

    @swagger_auto_schema(
        request_body=PrivateCityAliasSerializer,
        operation_id='Update City Alias',
        operation_description='Update an airbase which includes city and its alias.',
        responses={
            '200': openapi.Response('Update City Alias', PrivateCityAliasSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update bill of lading information
            :param request: request
            :return: Json of bill of lading.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCityAliasSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2005", message="City Alias: Invalid values.", errors=serializer.errors
            )

        try:
            alias = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            alias = serializer.update(instance=alias, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2007", message="City Alias: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = alias
        cache.delete(f'{self._cache_lookup_key}{alias.carrier.code}')
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete City Alias',
        operation_description='Delete an city alias for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete city alias from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            alias = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f'{self._cache_lookup_key}{alias.carrier.code}')
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        alias.delete()

        return Utility.json_response(data={"city_alias": self.kwargs["pk"], "message": "Successfully Deleted"})


class CarrierCityAliasUploadApi(UbbeMixin, APIView):
    """
        Upload carrier excel rate sheet.
    """

    _cache_lookup_key = "aliases_"

    @swagger_auto_schema(
        operation_id='Upload City Aliases',
        operation_description='Upload excel sheet of city alias for a carrier.',
        responses={
            '200': "City Alias has been uploaded.",
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Upload city alias for a carrier in excel format.
            :param request: request
            :return: Rate Sheet Lanes json.
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"city_alias": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="2010", message="City Alias: Missing 'carrier_code' parameter.", errors=errors
            )

        carrier_id = self.request.query_params["carrier_code"]
        uploaded_file = request.FILES['file']

        wb = load_workbook(uploaded_file)
        ws = wb.active

        try:
            CityAliasUpload().import_city_alias(
                workbook=ws,
                carrier_id=carrier_id
            )
        except ViewException as e:
            errors.append({"city_alias": f"City Alias upload failed: {e.message}"})
            return Utility.json_error_response(code="2011", message="City Alias upload failed", errors=errors)

        cache.delete(f'{self._cache_lookup_key}{carrier_id}')

        return Utility.json_response(data={"message": "City Alias has been uploaded."})
