"""
    Title: Sub Account Apis
    Description: This file will contain all functions for sub account api.
    Created: November 25, 2021
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
from api.models import SubAccount
from api.serializers_v3.private.account.sub_account_serializers import PrivateSubAccountSerializer, \
    PrivateCreateSubAccountSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class SubAccountApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'system', 'contact__name', 'contact__company_name', 'contact__email', 'address__city', 'address__address',
        'address__postal_code', 'bc_customer_code', 'bc_file_owner', 'id_prefix'
    ]

    # Customs
    _cache_lookup_key = "sub_accounts"

    def get_queryset(self):
        """
            Get initial sub accounts queryset and apply query params to the queryset.
            :return:
        """

        sub_accounts = cache.get(self._cache_lookup_key)

        if not sub_accounts:
            sub_accounts = SubAccount.objects.select_related(
                "client_account",
                "address__province__country",
                "contact",
                "markup",
            ).all().order_by("contact__company_name")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, sub_accounts, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'system' in self.request.query_params:
            sub_accounts = sub_accounts.filter(system=self.request.query_params["system"])

        if 'is_default' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_default=self.request.query_params["is_default"])

        if 'is_bc_push' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_bc_push=self.request.query_params["is_bc_push"])

        if 'is_account_id' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_account_id=self.request.query_params["is_account_id"])

        if 'is_dangerous_good' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_dangerous_good=self.request.query_params["is_dangerous_good"])

        if 'is_pharma' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_pharma=self.request.query_params["is_pharma"])

        if 'is_metric_included' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_metric_included=self.request.query_params["is_metric_included"])

        if 'is_bbe' in self.request.query_params:
            sub_accounts = sub_accounts.filter(is_bbe=self.request.query_params["is_bbe"])

        return sub_accounts

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'system',
                openapi.IN_QUERY,
                description="ubbe (UB), Fetchable (FE), DeliverEase (DE), or Thrid Party (TP)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_default', openapi.IN_QUERY, description="Default account foe the system.", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_bc_push', openapi.IN_QUERY, description="Pushing Shipments to BC.", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_account_id', openapi.IN_QUERY, description="Generate Unique IDs", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_dangerous_good', openapi.IN_QUERY, description="Allowed to do DGs", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_pharma', openapi.IN_QUERY, description="Allowed to do pharma", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_metric_included', openapi.IN_QUERY, description="Includes in goals", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_bbe', openapi.IN_QUERY, description="Is BBE account.", type=openapi.TYPE_BOOLEAN
            )
        ],
        operation_id='Get Sub Accounts',
        operation_description='Get a list of sub accounts for the system which contains information regarding address, '
                              'main contact, account number, and other settings for the account.',
        responses={
            '200': openapi.Response('Get Sub Accounts', PrivateSubAccountSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get sub accounts based on the allowed parameters and search params.
            :return:
        """

        sub_accounts = self.get_queryset()
        sub_accounts = self.filter_queryset(queryset=sub_accounts)
        serializer = PrivateSubAccountSerializer(sub_accounts, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateSubAccountSerializer,
        operation_id='Create Sub Account',
        operation_description='Create an sub account which contains information regarding address, main contact, '
                              'account number, and other settings for the account',
        responses={
            '200': openapi.Response('Create Sub Account', PrivateSubAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new sub account.
            :param request: request
            :return: json of sub account.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateSubAccountSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3500", message="SubAccount: Invalid values.", errors=serializer.errors
            )

        try:
            sub_account = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3501", message="SubAccount: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateSubAccountSerializer(instance=sub_account, many=False)
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class SubAccountDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put']

    # Customs
    _cache_lookup_key = "sub_accounts"
    _cache_lookup_key_individual = "sub_accounts_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = SubAccount.objects.select_related(
                "client_account",
                "address__province__country",
                "contact",
                "markup",
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Sub Account',
        operation_description='Get a sub account for the system which contains information regarding address, '
                              'main contact, account number, and other settings for the account.',
        responses={
            '200': openapi.Response('Get Sub Account', PrivateSubAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get sub account information.
            :return: Json of sub account.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_sub_accounts = cache.get(lookup_key)

        if not cached_sub_accounts:

            try:
                sub_account = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateSubAccountSerializer(instance=sub_account, many=False)
            cached_sub_accounts = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_sub_accounts, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_sub_accounts)

    @swagger_auto_schema(
        request_body=PrivateSubAccountSerializer,
        operation_id='Update Sub Account',
        operation_description='Update a sub account for the system which contains information regarding address, '
                              'main contact, account number, and other settings for the account.',
        responses={
            '200': openapi.Response('Update Sub Account', PrivateSubAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update sub account information
            :param request: request
            :return: Json of sub account.
        """
        errors = []
        json_data = request.data
        serializer = PrivateSubAccountSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3504", message="SubAccount: Invalid values.", errors=serializer.errors
            )

        try:
            sub_account = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            sub_account = serializer.update(instance=sub_account, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3506", message="SubAccount: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = sub_account
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)
