"""
    Title: Saved Contact api views
    Description: This file will contain all functions for saved contact api functions.
    Created: February 9, 2023
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
from api.models import SubAccount

from apps.books.models import SavedContact
from apps.books.serializers.saved_contact_serializer import (
    SavedContactSerializer,
    CreateSavedContactSerializer,
    UploadSavedContactSerializer,
)

from apps.common.pagination.paginations import ApiPagination, default_pagination
from apps.common.utilities.utilities import json_response

from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class SavedContactApi(UbbeMixin, ListCreateAPIView):
    """
    Saved Contact Api Endpoint
    """
    http_method_names = ["get", "post"]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "username",
        "contact__company_name",
        "contact__name",
        "contact__phone",
        "contact__email",
    ]

    # Customs
    _cache_lookup_key = "saved_contact"

    def get_queryset(self):
        """
        Get initial saved contact queryset and apply query params to the queryset.
        :return:
        """

        contact = cache.get(
            f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}"
        )

        if not contact:
            contact = SavedContact.objects.select_related(
                "account__contact"
            ).filter(account=self._sub_account).order_by("contact__name")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, contact, FIVE_HOURS_CACHE_TTL)

        if "username" in self.request.query_params:
            contact = contact.filter(username=self.request.query_params["username"])

        if "is_vendor" in self.request.query_params:
            contact = contact.filter(
                is_vendor=self.request.query_params["is_vendor"]
            )

        if "is_origin" in self.request.query_params:
            contact = contact.filter(
                is_origin=self.request.query_params["is_origin"]
            )

        if "is_destination" in self.request.query_params:
            contact = contact.filter(
                is_destination=self.request.query_params["is_destination"]
            )

        return contact

    @swagger_auto_schema(
        operation_id="Get Saved Contact",
        operation_description="Get a list of saved contacts available in the system.",
        responses={
            "200": openapi.Response(
                "Get Saved Contact", SavedContactSerializer(many=True)
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Get saved contacts for the system based on the allowed parameters and search params.
        :return:
        """

        contacts = self.get_queryset()
        contacts = self.filter_queryset(queryset=contacts)

        pagination = ApiPagination()
        page = pagination.paginate_queryset(queryset=contacts, request=request)

        if not page:
            serializer = SavedContactSerializer(contacts, many=True)
            return json_response(data=default_pagination(data=serializer.data))

        serializer = SavedContactSerializer(page, many=True)

        return json_response(data=pagination.get_paginated_response(serializer.data))

    @swagger_auto_schema(
        request_body=CreateSavedContactSerializer,
        operation_id="Create Saved Contact",
        operation_description="Create a saved contact for the system.",
        responses={
            "200": openapi.Response(
                "Create Saved Contact", CreateSavedContactSerializer
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new saved contacts.
        :param request: request
        :return: Json of saved contacts.
        """

        json_data = request.data
        serializer = CreateSavedContactSerializer(data=json_data, many=False)

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
            contact = serializer.create(validated_data=serializer.validated_data)
        except serializers.ValidationError as e:
            ret = {"code": "1200", "message": "Invalid values", "errors": e.detail}
            return json_response(error=True, message=ret)

        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")
        serializer = SavedContactSerializer(contact)

        return json_response(data=serializer.data)


class SavedContactDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete"]

    # Customs
    _cache_lookup_key = "saved_contact"
    _cache_lookup_key_individual = "saved_contact_"

    def get_object(self):
        """get_object
        Returns the object the view is displaying.
        """
        try:
            obj = SavedContact.objects.select_related("account").get(
                pk=self.kwargs["pk"]
            )
        except ObjectDoesNotExist:
            raise Http404

        return obj

    @swagger_auto_schema(
        operation_id="Get Saved Contact",
        operation_description="Get a saved contact available in the system.",
        responses={
            "200": openapi.Response(
                "Get Saved Contact", SavedContactSerializer(many=True)
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Get saved contact information.
        :return: Json of saved contact.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_contact = cache.get(lookup_key)

        if not cached_contact:
            serializer = SavedContactSerializer(instance=self.get_object(), many=False)
            cached_contact = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_contact, TWENTY_FOUR_HOURS_CACHE_TTL)

        return json_response(data=cached_contact)

    @swagger_auto_schema(
        request_body=SavedContactSerializer,
        operation_id="Update Saved Contact",
        operation_description="Update a saved contact in the system.",
        responses={
            "200": openapi.Response("Update Saved Contact", SavedContactSerializer),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def put(self, request, *args, **kwargs):
        """
        Update Saved Contact information
        :param request: request
        :return: Json of contact.
        """
        json_data = request.data
        serializer = SavedContactSerializer(data=json_data, many=False)

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
        operation_id="Delete Saved Contact",
        operation_description="Delete a saved contact.",
        responses={
            "200": "Successfully Deleted",
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete saved contact from the system.
        :param request: request
        :return: Success message.
        """

        contact = self.get_object()
        contact.delete()
        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return json_response(data={"message": "Successfully Deleted"})


class SavedContactUploadApi(UbbeMixin, CreateAPIView):
    http_method_names = ["post"]

    @swagger_auto_schema(
        operation_id="Upload Saved Contact",
        operation_description="Upload excel sheet of contacts.",
        request_body=UploadSavedContactSerializer,
        responses={
            "200": "Saved Contact has been uploaded.",
            "500": "Internal Server Error",
            "400": "Bad Request",
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Upload excel saved contacts.
        :param request: request
        :return: Saved Contacts json.
        """
        json_data = request.data
        serializer = UploadSavedContactSerializer(data=json_data, many=False)

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


class SavedContactProcessApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ["get", "post"]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "username",
        "contact__company_name",
        "contact__name",
        "contact__phone",
        "contact__email",
    ]

    # Customs
    _cache_lookup_key = "saved_contact_process"

    def get_queryset(self):
        """
        Get initial saved contact queryset and apply query params to the queryset.
        :return:
        """
        vendor = ""
        account_number = self._sub_account.subaccount_number

        if "is_vendor" in self.request.query_params:
            vendor = f"-vendor-{self.request.query_params['username']}"

        if "account_number" in self.request.query_params:
            account_number = self.request.query_params["account_number"]

        contact = cache.get(
            f"{self._cache_lookup_key}_{account_number}{vendor}"
        )

        if not contact:
            contact = SavedContact.objects.select_related(
                "account__contact"
            ).filter(account__subaccount_number=account_number)

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, contact, FIVE_HOURS_CACHE_TTL)

        if "username" in self.request.query_params:
            contact = contact.filter(username=self.request.query_params["username"])

        if "is_vendor" in self.request.query_params:
            contact = contact.filter(
                is_vendor=self.request.query_params["is_vendor"]
            )

        if "is_origin" in self.request.query_params:
            contact = contact.filter(
                is_origin=self.request.query_params["is_origin"]
            )

        if "is_destination" in self.request.query_params:
            contact = contact.filter(
                is_destination=self.request.query_params["is_destination"]
            )

        return contact

    @swagger_auto_schema(
        operation_id="Get Saved Contact",
        operation_description="Get a list of saved contacts available in the system.",
        responses={
            "200": openapi.Response(
                "Get Saved Contact", SavedContactSerializer(many=True)
            ),
            "400": "Bad Request",
            "500": "Internal Server Error",
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Get saved contacts for the system based on the allowed parameters and search params.
        :return:
        """

        contacts = self.get_queryset()
        contacts = self.filter_queryset(queryset=contacts)

        serializer = SavedContactSerializer(contacts, many=True)

        return json_response(data=serializer.data)
