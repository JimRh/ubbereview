"""
    Title: Saved Address api views
    Description: This file will contain all functions for saved address api functions.
    Created: January 27, 2023
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, serializers
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
)

from api.mixins.view_mixins import UbbeMixin

from apps.books.models import SavedAddress
from apps.books.serializers.saved_address_serializer import (
    SavedAddressSerializer,
    CreateSavedAddressSerializer,
    UploadSavedAddressSerializer,
)

from apps.common.pagination.paginations import ApiPagination, default_pagination
from apps.common.utilities.utilities import json_response

from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class SavedAddressApi(UbbeMixin, ListCreateAPIView):
    """
    Saved Address Api Endpoint
    """

    http_method_names = ["get", "post"]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "name",
        "username",
        "address__city",
        "address__address",
        "address__province__code",
        "address__province__name",
        "address__province__country__code",
        "address__province__country__name",
        "address__postal_code",
    ]

    _cache_lookup_key = "saved_address"

    def get_queryset(self):
        """
        Get initial saved address queryset and apply query params to the queryset.
        :return:
        """

        address = cache.get(
            f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}"
        )

        if not address:
            address = SavedAddress.objects.select_related(
                "address__province__country"
            ).filter(account=self._sub_account).order_by("name")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, address, FIVE_HOURS_CACHE_TTL)

        if "username" in self.request.query_params:
            address = address.filter(username=self.request.query_params["username"])

        if "is_vendor" in self.request.query_params:
            address = address.filter(
                is_vendor=self.request.query_params["is_vendor"]
            )

        if "is_origin" in self.request.query_params:
            address = address.filter(
                is_origin=self.request.query_params["is_origin"]
            )

        if "is_destination" in self.request.query_params:
            address = address.filter(
                is_destination=self.request.query_params["is_destination"]
            )

        return address

    @swagger_auto_schema(
        operation_id="Get Saved Address",
        operation_description="Get a list of saved addresses available in the system.",
        responses={
            "200": openapi.Response(
                "Get Saved Address", SavedAddressSerializer(many=True)
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Get saved addresses for the system based on the allowed parameters and search params.
        :return:
        """

        addresses = self.get_queryset()
        addresses = self.filter_queryset(queryset=addresses)

        pagination = ApiPagination()
        page = pagination.paginate_queryset(queryset=addresses, request=request)

        if not page:
            serializer = SavedAddressSerializer(addresses, many=True)
            return json_response(data=default_pagination(data=serializer.data))

        serializer = SavedAddressSerializer(page, many=True)

        return json_response(data=pagination.get_paginated_response(serializer.data))

    @swagger_auto_schema(
        request_body=CreateSavedAddressSerializer,
        operation_id="Create Saved Address",
        operation_description="Create a saved address for the system.",
        responses={
            "200": openapi.Response(
                "Create Saved Address", CreateSavedAddressSerializer
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new saved addresses.
        :param request: request
        :return: Json of saved addresses.
        """

        json_data = request.data
        serializer = CreateSavedAddressSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return json_response(
                message={
                    "code": "1200",
                    "message": "Invalid values",
                    "errors": serializer.errors,
                },
                error=True,
            )

        try:
            address = serializer.create(validated_data=serializer.validated_data)
        except serializers.ValidationError as e:
            ret = {"code": "1200", "message": "Invalid values", "errors": e.detail}
            return json_response(error=True, message=ret)

        vendor = ""

        if address.is_vendor:
            vendor = f"-vendor-{address.username}"

        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}{vendor}")
        cache.delete(f"{self._cache_lookup_key}_process_{self._sub_account.subaccount_number}{vendor}")
        serializer = SavedAddressSerializer(address)

        return json_response(data=serializer.data)


class SavedAddressDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete"]

    # Customs
    _cache_lookup_key = "saved_address"
    _cache_lookup_key_individual = "saved_address_"

    def get_object(self):
        """
        Returns the object the view is displaying.
        """

        try:
            obj = SavedAddress.objects.select_related("address__province__country").get(
                pk=self.kwargs["pk"]
            )
        except ObjectDoesNotExist:
            raise Http404

        return obj

    @swagger_auto_schema(
        operation_id="Get Saved Address",
        operation_description="Get a saved address available in the system.",
        responses={
            "200": openapi.Response(
                "Get Saved Address", SavedAddressSerializer(many=True)
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Get saved address information.
        :return: Json of saved address.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_address = cache.get(lookup_key)

        if not cached_address:
            serializer = SavedAddressSerializer(instance=self.get_object(), many=False)
            cached_address = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_address, TWENTY_FOUR_HOURS_CACHE_TTL)

        return json_response(data=cached_address)

    @swagger_auto_schema(
        request_body=SavedAddressSerializer,
        operation_id="Update Saved Address",
        operation_description="Update a saved address in the system.",
        responses={
            "200": openapi.Response("Update Saved Address", SavedAddressSerializer),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def put(self, request, *args, **kwargs):
        """
        Update Saved Address information
        :param request: request
        :return: Json of web hook.
        """
        json_data = request.data
        serializer = SavedAddressSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return json_response(
                message={
                    "code": "1204",
                    "message": "Invalid values",
                    "errors": serializer.errors,
                },
                error=True,
            )

        try:
            serializer.instance = serializer.update(
                instance=self.get_object(), validated_data=serializer.validated_data
            )
        except serializers.ValidationError as e:
            ret = {"code": "1200", "message": "Invalid values", "errors": e.detail}
            return json_response(error=True, message=ret)

        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id="Delete Saved Address",
        operation_description="Delete a saved address.",
        responses={
            "200": "Successfully Deleted",
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete saved address from the system
        :param request: request
        :return: Success message.
        """

        address = self.get_object()
        address.delete()
        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return json_response(data={"message": "Successfully Deleted"})


class SavedAddressUploadApi(UbbeMixin, CreateAPIView):
    http_method_names = ["post"]

    @swagger_auto_schema(
        operation_id="Upload Saved Address",
        operation_description="Upload excel sheet of addresses.",
        request_body=UploadSavedAddressSerializer,
        responses={
            "200": "Saved Address has been uploaded.",
            "500": "Internal Server Error",
            "400": "Bad Request",
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Upload excel saved addresses.
        :param request: request
        :return: Saved Addresses json.
        """

        json_data = request.data
        serializer = UploadSavedAddressSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return json_response(
                message={
                    "code": "1204",
                    "message": "Invalid values",
                    "errors": serializer.errors,
                },
                error=True,
            )

        try:
            serializer.validated_data["account"] = self._sub_account
            ret = serializer.create(validated_data=serializer.validated_data)
        except serializers.ValidationError as e:
            ret = {"code": "1200", "message": "Invalid values", "errors": e.detail}
            return json_response(error=True, message=ret)

        return json_response(data=ret)


class SavedAddressProcessApi(UbbeMixin, ListCreateAPIView):
    """
    Saved Address Process Api Endpoint
    """

    http_method_names = ["get", "post"]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "name",
        "username",
        "address__city",
        "address__address",
        "address__province__code",
        "address__province__name",
        "address__province__country__code",
        "address__province__country__name",
        "address__postal_code",
    ]

    _cache_lookup_key = "saved_address_process"

    def get_queryset(self):
        """
        Get initial saved address queryset and apply query params to the queryset.
        :return:
        """
        vendor = ""
        account_number = self._sub_account.subaccount_number

        if "account_number" in self.request.query_params:
            account_number = self.request.query_params["account_number"]

        if "is_vendor" in self.request.query_params:
            vendor = f"-vendor-{self.request.query_params['username']}"
        address = cache.get(
            f"{self._cache_lookup_key}_{account_number}{vendor}"
        )

        if not address:
            address = SavedAddress.objects.select_related(
                "address__province__country"
            ).filter(account__subaccount_number=account_number)

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, address, FIVE_HOURS_CACHE_TTL)

        if "username" in self.request.query_params:
            address = address.filter(username=self.request.query_params["username"])

        if "is_vendor" in self.request.query_params:
            address = address.filter(
                is_vendor=self.request.query_params["is_vendor"]
            )

        if "is_origin" in self.request.query_params:
            address = address.filter(
                is_origin=self.request.query_params["is_origin"]
            )

        if "is_destination" in self.request.query_params:
            address = address.filter(
                is_destination=self.request.query_params["is_destination"]
            )

        return address

    @swagger_auto_schema(
        operation_id="Get Saved Address",
        operation_description="Get a list of all saved addresses available in the system.",
        responses={
            "200": openapi.Response(
                "Get Saved Address", SavedAddressSerializer(many=True)
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Get saved addresses for the system based on the allowed parameters and search params.
        :return:
        """

        addresses = self.get_queryset()
        addresses = self.filter_queryset(queryset=addresses)

        serializer = SavedAddressSerializer(addresses, many=True)

        return json_response(data=serializer.data)

