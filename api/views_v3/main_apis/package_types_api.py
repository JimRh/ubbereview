"""
    Title: Package Type Api Views V3
    Description: This file will contain all api views for package type.
    Created: Nov 18, 2021
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
from api.models import PackageType
from api.serializers_v3.common.package_type_serializer import PackageTypeSerializer
from api.utilities.utilities import Utility
from brain.settings import FIVE_HOURS_CACHE_TTL


class PackageTypeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']

    # Customs
    _cache_lookup_key = "package_types_"

    def get_queryset(self):
        """
            Get initial package type queryset and apply query params to the queryset.
            :return:
        """

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            package_types = PackageType.objects.select_related("account__user").filter(
                account__user__username=self.request.query_params["account"]
            )
        else:
            lookup = f"{self._cache_lookup_key}{self._sub_account.client_account.user.username}"
            package_types = cache.get(lookup)

            if not package_types:
                package_types = PackageType.objects.select_related("account__user").filter(
                    account=self._sub_account.client_account
                )

                # Store metrics for 5 hours
                cache.set(lookup, package_types, FIVE_HOURS_CACHE_TTL)

        if 'is_common' in self.request.query_params:
            package_types = package_types.filter(is_common=self.request.query_params["is_common"])

        if 'is_dangerous_good' in self.request.query_params:
            package_types = package_types.filter(is_dangerous_good=self.request.query_params["is_dangerous_good"])

        if 'is_pharma' in self.request.query_params:
            package_types = package_types.filter(is_pharma=self.request.query_params["is_pharma"])

        if not self._sub_account.is_pharma:
            package_types = package_types.filter(is_pharma=False)

        if 'is_active' in self.request.query_params:
            package_types = package_types.filter(is_active=self.request.query_params["is_active"])

        return package_types.order_by("name")

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PackageTypeSerializer
        else:
            return PackageTypeSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'is_common', openapi.IN_QUERY, description="Only Common", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_dangerous_good', openapi.IN_QUERY, description="Only Dangerous Goods", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_pharma', openapi.IN_QUERY, description="Only Pharma", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_active', openapi.IN_QUERY, description="Only Active", type=openapi.TYPE_BOOLEAN
            )
        ],
        operation_id='Get Package Types',
        operation_description='Get a list of package types from the system.',
        responses={
            '200': openapi.Response('Get Package Types', PackageTypeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get package types based on the allowed parameters and determine.
            :return:
        """

        package_types = self.get_queryset()
        package_types = self.filter_queryset(queryset=package_types)
        serializer = self.get_serializer_class()
        serializer = serializer(package_types, many=True)

        data = serializer.data

        for pack in data:

            if not pack["is_dangerous_good"]:
                continue

            pack["is_dangerous_good"] = self._sub_account.is_dangerous_good

        return Utility.json_response(data=data)

    @swagger_auto_schema(
        request_body=PackageTypeSerializer,
        operation_id='Create Package Type',
        operation_description='Create a package type for the system.',
        responses={
            '200': openapi.Response('Create Package Type', PackageTypeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new Package Type.
            :param request: request
            :return: Package Type json.
        """
        errors = []
        json_data = request.data
        serializer = PackageTypeSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1100", message="Package Types: Invalid values.", errors=serializer.errors
            )

        try:
            package_type = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1101", message="Package Types: failed to save.", errors=errors)
        except ViewException as e:
            errors.append({"package_types": e.message})
            return Utility.json_error_response(code="1102", message="Package Types: failed to save.", errors=errors)

        serializer.instance = package_type
        cache.delete(f"{self._cache_lookup_key}{package_type.account.user.username}")

        return Utility.json_response(data=serializer.data)


class PackageTypeDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "package_types_"
    _cache_lookup_key_individual = "package_type_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = PackageType.objects.select_related("account__user").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"package_type": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1103", message="Package Type: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Package Type',
        operation_description='Get a package type from the system.',
        responses={
            '200': openapi.Response('Get Package Type', PackageTypeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get package type information.
            :return: Json of package type.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_package_type = cache.get(lookup_key)

        if not cached_package_type:

            try:
                package_type = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PackageTypeSerializer(instance=package_type, many=False)
            cached_package_type = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_package_type, FIVE_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_package_type)

    @swagger_auto_schema(
        request_body=PackageTypeSerializer,
        operation_id='Update Package Type',
        operation_description='Update an package type information.',
        responses={
            '200': openapi.Response('Update Package Type', PackageTypeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update package type information
            :param request: request
            :return: Json of package type.
        """
        errors = []
        json_data = request.data
        serializer = PackageTypeSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1104", message="Package Types: Invalid values.", errors=serializer.errors
            )

        try:
            package_type = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            package_type = serializer.update(instance=package_type, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1106", message="Package Type: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code="1107", message="Package Type: failed to update.", errors=errors)

        serializer.instance = package_type
        cache.delete(f"{self._cache_lookup_key}{package_type.account.user.username}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Package Type',
        operation_description='Delete an package type.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete package type from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            package_type = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f"{self._cache_lookup_key}{package_type.account.user.username}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        package_type.delete()

        return Utility.json_response(data={"package_type": self.kwargs["pk"], "message": "Successfully Deleted"})
