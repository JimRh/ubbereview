"""
    Title: Api Permissions api views
    Description: This file will contain all functions for api permissions api functions.
    Created: February 15, 2022
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
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView

from api.apis.uploads.api_permissions_upload import ApiPermissionUpload
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import ApiPermissions
from api.serializers_v3.private.admin.api_permissions_serializers import PrivateApiPermissionsSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ApiPermissionsApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'reason']

    # Customs
    _cache_lookup_key = "admin_api_permission"

    def get_queryset(self):
        """
            Get initial apis queryset and apply query params to the queryset.
            :return:
        """

        apis = cache.get(self._cache_lookup_key)

        if not apis:
            apis = ApiPermissions.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, apis, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'category' in self.request.query_params:
            apis = apis.filter(category=self.request.query_params["category"])

        if 'is_active' in self.request.query_params:
            apis = apis.filter(is_active=self.request.query_params["is_active"])

        if 'is_admin' in self.request.query_params:
            apis = apis.filter(is_admin=self.request.query_params["is_admin"])

        return apis

    @swagger_auto_schema(
        operation_id='Get Api Permissions',
        operation_description='Get all Api permissions for the system including if they are on or off.',
        responses={
            '200': openapi.Response('Api Permissions', PrivateApiPermissionsSerializer(many=True)),
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get api permissions for the system based on the allowed parameters and search params.
            :return:
        """

        apis = self.get_queryset()
        apis = self.filter_queryset(queryset=apis)
        serializer = PrivateApiPermissionsSerializer(apis, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Create Api Permission',
        operation_description='Create an permission for the system, must relate to an endpoint to function properly.',
        request_body=PrivateApiPermissionsSerializer,
        responses={
            '200': openapi.Response('Create Api Permission', PrivateApiPermissionsSerializer),
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new api permission.
            :param request: request
            :return: Json list of api permission.
        """
        errors = []

        json_data = request.data
        serializer = PrivateApiPermissionsSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="7900", message="Api Permission: Invalid values.", errors=serializer.errors
            )

        try:
            api = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="7901", message="Api Permission: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = api
        cache.delete(self._cache_lookup_key)
        return Utility.json_response(data=serializer.data)


class ApiPermissionsDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "admin_api_permission"
    _cache_lookup_key_individual = "admin_api_permission_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = ApiPermissions.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api_permission": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="7902", message="Api Permission: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Api Permission',
        operation_description='Get an Api permission for the system including if they are on or off.',
        responses={
            '200': openapi.Response('Api Permission', PrivateApiPermissionsSerializer),
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get api permission information.
            :return: Json of api permission.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_api = cache.get(lookup_key)

        if not cached_api:

            try:
                api = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateApiPermissionsSerializer(instance=api, many=False)
            cached_api = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_api, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_api)

    @swagger_auto_schema(
        request_body=PrivateApiPermissionsSerializer,
        operation_id='Update Api Permission',
        operation_description='Update an api permission in the system containing if its on or off and the reason.',
        responses={
            '200': openapi.Response('Update Api Permission', PrivateApiPermissionsSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update api permission information
            :param request: request
            :return: Json of api permission.
        """
        errors = []
        json_data = request.data
        serializer = PrivateApiPermissionsSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="7903", message="Api Permission: Invalid values.", errors=serializer.errors
            )

        try:
            api = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            api = serializer.update(instance=api, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="7904", message="Api Permission: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = api
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Api Permission',
        operation_description='Delete an api permission from the system.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete api permission from the system.
            :param request: request
            :return: Success api permission.
        """

        try:
            obj = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        obj.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"api_permission": self.kwargs["pk"], "message": "Successfully Deleted"})


class ApiPermissionUploadApi(UbbeMixin, CreateAPIView):
    """
        Upload carrier excel rate sheet.
    """
    # TODO - Temp view to mass upload permissions -> Either Delete or add proper serializer.
    http_method_names = ['post']

    # Customs
    _cache_lookup_key = "admin_api_permission"
    _cache_lookup_key_individual = "admin_api_permission_"

    @swagger_auto_schema(
        operation_id='Upload Api Permission',
        operation_description='Upload excel sheet of api permissions for the system, each line must relate to an '
                              'endpoint a function properly.',
        request_body=PrivateApiPermissionsSerializer,
        responses={
            '200': openapi.Response('Upload Api Permission', PrivateApiPermissionsSerializer),
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Upload api permission from excel sheet.
            :param request: request
            :return: Success Message.
        """

        uploaded_file = request.FILES['file']
        wb = load_workbook(uploaded_file)
        ws = wb.active

        try:
            ApiPermissionUpload().import_errors(workbook=ws)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f'{self._cache_lookup_key}')
        cache.delete_pattern(f'{self._cache_lookup_key}*')

        return Utility.json_response(data={"message": "Api Permissions has been uploaded."})
