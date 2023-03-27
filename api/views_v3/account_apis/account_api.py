"""
    Title: Account api views
    Description: This file will contain all functions for account serializers.
    Created: November 18, 2021
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
from api.models import Account
from api.serializers_v3.private.account.account_serializers import PrivateAccountSerializer
from api.utilities.utilities import Utility
from brain.settings import FIVE_HOURS_CACHE_TTL


class AccountApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']

    # Customs
    _cache_lookup_key = "accounts"

    def get_queryset(self):
        """
            Get initial account queryset and apply query params to the queryset.
            :return:
        """

        accounts = cache.get(self._cache_lookup_key)

        if not accounts:
            accounts = Account.objects.select_related("user").all().order_by("user")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, accounts, FIVE_HOURS_CACHE_TTL)

        if 'subaccounts_allowed' in self.request.query_params:
            accounts = accounts.filter(subaccounts_allowed=self.request.query_params["subaccounts_allowed"])

        return accounts

    @swagger_auto_schema(
        query_serializer=PrivateAccountSerializer,
        operation_id='Get Accounts',
        operation_description='Get accounts for the system containing main contact details, allowed carriers and if '
                              'the account is allowed sub accounts. You are able to also search "username", "first '
                              'name", "last name", and "email" to narrow down the results.',
        responses={
            '200': openapi.Response('Get Accounts', PrivateAccountSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get accounts for the system based on the allowed parameters and search params.
            :return: lists of accounts
        """

        accounts = self.get_queryset()
        accounts = self.filter_queryset(queryset=accounts)
        serializer = PrivateAccountSerializer(accounts, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateAccountSerializer,
        operation_id='Create Account',
        operation_description='Create an account for the system that will contain the main contact details, what '
                              'carriers are allowed and if the account is allowed sub accounts.',
        responses={
            '200': openapi.Response('Create Account', PrivateAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new account.
            :param request: request
            :return: json of account.
        """
        errors = []
        json_data = request.data
        serializer = PrivateAccountSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3400", message="Account: Invalid values.", errors=serializer.errors
            )

        try:
            account = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3401", message="Account: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = account
        cache.delete(self._cache_lookup_key)
        return Utility.json_response(data=serializer.data)


class AccountDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get']

    # Customs
    _cache_lookup_key = "accounts"
    _cache_lookup_key_individual = "accounts_"
    _sub_account = None

    @swagger_auto_schema(
        operation_id='Get Account',
        operation_description='Get an account for the system containing main contact details, allowed carriers and if '
                              'the account is allowed sub accounts.',
        responses={
            '200': openapi.Response('Get Account', PrivateAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get account information.
            :return: Json of account.
        """
        errors = []
        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_account = cache.get(lookup_key)

        if not cached_account:
            try:
                account = Account.objects.select_related("user").get(pk=self.kwargs["pk"])
            except ObjectDoesNotExist:
                errors.append({"account": f'{self.kwargs["pk"]} not found or you do not have permission.'})
                return Utility.json_error_response(code="3403", message="Account: Not Found.", errors=errors)

            serializer = PrivateAccountSerializer(instance=account, many=False)
            cached_account = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_account, FIVE_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_account)
