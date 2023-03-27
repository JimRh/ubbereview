"""
    Title: Api api views
    Description: This file will contain all functions for api api functions.
    Created: November 19, 2021
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
from api.models import API
from api.serializers_v3.private.admin.api_serializers import PrivateApiSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ApiApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    # Customs
    _cache_lookup_key = "admin_api"

    def get_queryset(self):
        """
            Get initial apis queryset and apply query params to the queryset.
            :return:
        """

        apis = cache.get(self._cache_lookup_key)

        if not apis:
            apis = API.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, apis, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'category' in self.request.query_params:
            apis = apis.filter(category=self.request.query_params["category"])

        if 'active' in self.request.query_params:
            apis = apis.filter(active=self.request.query_params["active"])

        return apis

    @swagger_auto_schema(
        operation_id='Get Apis',
        operation_description='Get a list of apis for the system, these contain functionality apis such as carrier '
                              'apis, or other functionality to turn off.',
        responses={
            '200': openapi.Response('Get Apis', PrivateApiSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get markups for the system based on the allowed parameters and search params.
            :return:
        """

        apis = self.get_queryset()
        apis = self.filter_queryset(queryset=apis)
        serializer = PrivateApiSerializer(apis, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateApiSerializer,
        operation_id='Create Api',
        operation_description='Create an api that will control functional logic to turn off and on.',
        responses={
            '200': openapi.Response('Create Api', PrivateApiSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new api.
            :param request: request
            :return: Json list of api.
        """
        errors = []

        json_data = request.data
        serializer = PrivateApiSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(code="4100", message="Api: Invalid values.", errors=serializer.errors)

        try:
            api = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4101", message="Api: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = api
        cache.delete(self._cache_lookup_key)
        return Utility.json_response(data=serializer.data)


class ApiDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "admin_api"
    _cache_lookup_key_individual = "admin_api_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = API.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Api',
        operation_description='Get a api form the system that contains information such as name and if its on '
                              'or off and what time of api it is.',
        responses={
            '200': openapi.Response('Get Api', PrivateApiSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get api information.
            :return: Json of api.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_api = cache.get(lookup_key)

        if not cached_api:

            try:
                api = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateApiSerializer(instance=api, many=False)
            cached_api = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_api, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_api)

    @swagger_auto_schema(
        request_body=PrivateApiSerializer,
        operation_id='Update Api',
        operation_description='Update an api naming or turn it on or off.',
        responses={
            '200': openapi.Response('Update Api', PrivateApiSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update api information
            :param request: request
            :return: Json of api.
        """
        errors = []
        json_data = request.data
        serializer = PrivateApiSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(code="4104", message="Api: Invalid values.", errors=serializer.errors)

        try:
            api = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            api = serializer.update(instance=api, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4106", message="Api: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = api
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        cache.delete(f"api_active_{api.name}")

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Api',
        operation_description='Delete an api for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete api from the system.
            :param request: request
            :return: Success api.
        """

        try:
            api = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        cache.delete(f"api_active_{api.name}")

        api.delete()

        return Utility.json_response(data={"api": self.kwargs["pk"], "message": "Successfully Deleted"})
