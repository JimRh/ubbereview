"""
    Title: Saved Package api views
    Description: This file will contain all functions for saved packages api functions.
    Created: October 26, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import SavedPackage
from api.serializers_v3.common.saved_package_serializers import SavedPackageSerializer, UploadSavedPackageSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class SavedPackageApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post', 'delete']
    filter_backends = [filters.SearchFilter]
    search_fields = ['width', 'length', 'height', 'weight', 'description', 'package_type', 'box_type']

    # Customs
    _cache_lookup_key = "saved_package"
    _cache_lookup_key_individual = "saved_package_"

    def get_queryset(self):
        """
            Get initial packages queryset and apply query params to the queryset.
            :return:
        """

        packages = cache.get(f"{self._cache_lookup_key}_{str(self._sub_account.subaccount_number)}")

        if not packages:
            packages = SavedPackage.objects.select_related("sub_account").filter(sub_account=self._sub_account)

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, packages, FIVE_HOURS_CACHE_TTL)

        if 'box_type' in self.request.query_params:
            packages = packages.filter(box_type=self.request.query_params["box_type"])

        return packages

    @swagger_auto_schema(
        operation_id='Get Saved Packages',
        operation_description='Get a list of saved packages available in the system.',

        responses={
            '200': openapi.Response('Get Saved Packages', SavedPackageSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get saved packages for the system based on the allowed parameters and search params.
            :return:
        """

        packages = self.get_queryset()
        packages = self.filter_queryset(queryset=packages)
        serializer = SavedPackageSerializer(packages, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=SavedPackageSerializer,
        operation_id='Create Saved Package',
        operation_description='Create a saved package for the system.',
        responses={
            '200': openapi.Response('Create Saved Package', SavedPackageSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new saved package.
            :param request: request
            :return: Json of saved packages.
        """
        errors = []
        json_data = request.data
        serializer = SavedPackageSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1200", message="Saved Package: Invalid values.", errors=serializer.errors
            )

        try:
            package = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1201", message="Saved Package: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = package
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)

    def delete(self, request, *args, **kwargs):
        """
            Delete saved package from the system.
            :param request: request
            :return: Success message.
        """

        json_data = request.data

        SavedPackage.objects.filter(sub_account=self._sub_account, box_type=json_data["box_type"]).delete()
        cache.delete(self._cache_lookup_key)
        cache.delete_pattern(f"{self._cache_lookup_key_individual}*")

        return Utility.json_response(data={"saved_package": "all", "message": "Successfully Deleted"})


class SavedPackageDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "saved_package"
    _cache_lookup_key_individual = "saved_package_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = SavedPackage.objects.select_related("sub_account").get(
                sub_account=self._sub_account, pk=self.kwargs["pk"]
            )
        except ObjectDoesNotExist:
            errors.append({"Saved Package": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1103", message="Saved Package: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Saved Package',
        operation_description='Get a saved package available in the system.',
        responses={
            '200': openapi.Response('Get Saved Packages', SavedPackageSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get saved package information.
            :return: Json of saved package.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_package = cache.get(lookup_key)

        if not cached_package:

            try:
                package = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = SavedPackageSerializer(instance=package, many=False)
            cached_package = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_package, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_package)

    @swagger_auto_schema(
        request_body=SavedPackageSerializer,
        operation_id='Update Saved Package',
        operation_description='Update a saved package in the system.',
        responses={
            '200': openapi.Response('Update Saved Package', SavedPackageSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update saved package information
            :param request: request
            :return: Json of saved package.
        """
        errors = []
        json_data = request.data
        serializer = SavedPackageSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1204", message="Saved Package: Invalid values.", errors=serializer.errors
            )

        try:
            package = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            package = serializer.update(instance=package, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1206", message="Saved Package: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = package
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Saved Package',
        operation_description='Delete a saved package.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete saved package from the system.
            :param request: request
            :return: Success message.
        """

        try:
            package = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        package.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"saved_package": self.kwargs["pk"], "message": "Successfully Deleted"})


class SavedPackageUploadApi(UbbeMixin, CreateAPIView):
    http_method_names = ['post']

    @swagger_auto_schema(
        operation_id='Upload Saved Package',
        operation_description='Upload excel sheet of packages.',
        request_body=UploadSavedPackageSerializer,
        responses={
            '200': 'Saved Package has been uploaded.',
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Upload excel saved packages.
            :param request: request
            :return: Saved Packages json.
        """
        errors = []
        json_data = request.data
        serializer = UploadSavedPackageSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6400", message="SavedPackageUpload: Invalid values.", errors=serializer.errors
            )

        try:
            ret = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6401", message="SavedPackageUpload: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        connection.close()
        return Utility.json_response(data=ret)
