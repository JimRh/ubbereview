"""
    Title: Error Code api views
    Description: This file will contain all functions for error code functions.
    Created: December 07, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from openpyxl import load_workbook
from pytz import utc
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView

from api.apis.uploads.error_code_upload import ErrorCodeUpload
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import ErrorCode
from api.serializers_v3.private.admin.error_code_serializers import PrivateErrorCodeSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class ErrorCodeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['error_id', 'system', 'source', 'type', 'code', 'name', 'actual_message', 'solution', 'location']

    # Customs
    _cache_lookup_key = "error_codes"

    def get_queryset(self):
        """
            Get initial error code queryset and apply query params to the queryset.
            :return:
        """

        error_codes = cache.get(self._cache_lookup_key)

        if not error_codes:
            error_codes = ErrorCode.objects.all().order_by("code")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, error_codes, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'system' in self.request.query_params:
            error_codes = error_codes.filter(system=self.request.query_params["system"])

        return error_codes

    @swagger_auto_schema(
        operation_id='Get Error Codes',
        operation_description='Get a list of error codes for the system which contains information about errors and '
                              'potential solutions and location in the code base. ',
        responses={
            '200': openapi.Response('Get Error Codes', PrivateErrorCodeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get error codes for the system based on the allowed parameters and search params.
            :return:
        """

        error_codes = self.get_queryset()
        error_codes = self.filter_queryset(queryset=error_codes)
        serializer = PrivateErrorCodeSerializer(error_codes, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateErrorCodeSerializer,
        operation_id='Create Error Code',
        operation_description='Create a error code which contains information about errors and potential solutions '
                              'and location in the code base.',
        responses={
            '200': openapi.Response('Create Error Code', PrivateErrorCodeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new error code.
            :param request: request
            :return: Json of error code.
        """
        errors = []
        json_data = request.data
        serializer = PrivateErrorCodeSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4500", message="Error Codes: Invalid values.", errors=serializer.errors
            )

        try:
            error_codes = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4501", message="Error Codes: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = error_codes
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class ErrorCodeDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "error_codes"
    _cache_lookup_key_individual = "error_codes_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = ErrorCode.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Error Code',
        operation_description='Get a error code for the system which contains information about errors and '
                              'potential solutions and location in the code base. ',
        responses={
            '200': openapi.Response('Get Error Code', PrivateErrorCodeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get error code information.
            :return: Json of error code.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_error_code = cache.get(lookup_key)

        if not cached_error_code:

            try:
                error_code = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateErrorCodeSerializer(instance=error_code, many=False)
            cached_error_code = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_error_code, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_error_code)

    @swagger_auto_schema(
        request_body=PrivateErrorCodeSerializer,
        operation_id='Update Error Code',
        operation_description='Update an error code which contains information about errors and potential solutions '
                              'and location in the code base.',
        responses={
            '200': openapi.Response('Update Error Code', PrivateErrorCodeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update error code information
            :param request: request
            :return: Json of error code.
        """
        errors = []
        json_data = request.data
        json_data["updated_date"] = datetime.datetime.now(tz=utc).isoformat()
        serializer = PrivateErrorCodeSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4504", message="Error Codes: Invalid values.", errors=serializer.errors
            )

        try:
            error_code = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            error_code = serializer.update(instance=error_code, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4506", message="Error Codes: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = error_code
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Error Code',
        operation_description='Delete an error code for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete error code from the system.
            :param request: request
            :return: Success error code.
        """

        try:
            error_code = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        error_code.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"error_code": self.kwargs["pk"], "message": "Successfully Deleted"})


class ErrorCodeUploadApi(UbbeMixin, CreateAPIView):
    """
        Upload carrier excel rate sheet.
    """
    http_method_names = ['post']

    # Customs
    _cache_lookup_key = "error_codes"
    _cache_lookup_key_individual = "error_codes_"

    @swagger_auto_schema(
        operation_id='Upload Error Codes',
        operation_description='Upload excel sheet of error codes for the system.',
        responses={
            '200': 'Error Codes has been uploaded.',
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Upload Error Codes from excel sheet.
            :param request: request
            :return: Success Message.
        """

        uploaded_file = request.FILES['file']
        wb = load_workbook(uploaded_file)
        ws = wb.active

        try:
            ErrorCodeUpload().import_errors(workbook=ws)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f'{self._cache_lookup_key}')
        cache.delete_pattern(f'{self._cache_lookup_key}*')

        return Utility.json_response(data={"message": "Error Codes has been uploaded."})
