"""
    Title: 5T Skyline Account Api
    Description: This file will contain all functions for 5T skyline account apis.
    Created: December 02, 2021
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
from api.models import SkylineAccount
from api.serializers_v3.private.cn.skyline_account_serializers import PrivateSkylineAccountSerializer, \
    PrivateCreateSkylineAccountSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CNSkylineAccountApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['skyline_account', 'customer_id', 'sub_account__subaccount_number']

    # Customs
    _cache_lookup_key = "cn_skyline_account"

    def get_queryset(self):
        """
            Get initial 5t skyline accounts queryset and apply query params to the queryset.
            :return:
        """

        accounts = cache.get(self._cache_lookup_key)

        if not accounts:
            accounts = SkylineAccount.objects.select_related("sub_account__contact").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, accounts, TWENTY_FOUR_HOURS_CACHE_TTL)

        return accounts

    @swagger_auto_schema(
        operation_id='Get CN Skyline Accounts',
        operation_description='Get a list of canadian north skyline accounts.',
        responses={
            '200': openapi.Response('Get CN Skyline Accounts', PrivateSkylineAccountSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get skyline accounts for a carrier based on the allowed parameters and search params.
            :return:
        """

        accounts = self.get_queryset()
        accounts = self.filter_queryset(queryset=accounts)
        serializer = PrivateSkylineAccountSerializer(accounts, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateSkylineAccountSerializer,
        operation_id='Create CN Skyline Account',
        operation_description='Create a canadian north skyline account.',
        responses={
            '200': openapi.Response('Create CN Skyline Account', PrivateSkylineAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new 5t skyline account.
            :param request: request
            :return: 5t skyline account json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateSkylineAccountSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="5700", message="CN Account: Invalid values.", errors=serializer.errors
            )

        try:
            account = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="5701", message="CN Account: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateSkylineAccountSerializer(instance=account, many=False)
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class CNSkylineAccountDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "cn_skyline_account"
    _cache_lookup_key_individual = "cn_skyline_account_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = SkylineAccount.objects.select_related("sub_account__contact").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"cn_account": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="5703", message="CN Account: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get CN Skyline Account',
        operation_description='Get a canadian north skyline account.',
        responses={
            '200': openapi.Response('Get CN Skyline Account', PrivateSkylineAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get 5t skyline account information.
            :return: Json of 5t skyline account
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_account = cache.get(lookup_key)

        if not cached_account:

            try:
                account = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateSkylineAccountSerializer(instance=account, many=False)
            cached_account = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_account, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_account)

    @swagger_auto_schema(
        request_body=PrivateSkylineAccountSerializer,
        operation_id='Update CN Interline lane',
        operation_description='Update a canadian north skyline account.',
        responses={
            '200': openapi.Response('Update CN Interline lane', PrivateSkylineAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update 5t skyline account information
            :param request: request
            :return: Json of 5t skyline account.
        """
        errors = []
        json_data = request.data
        serializer = PrivateSkylineAccountSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="5704", message="CN Account: Invalid values.", errors=serializer.errors
            )

        try:
            account = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            account = serializer.update(instance=account, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="5706", message="CN Account: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = account
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete CN Skyline Account',
        operation_description='Delete an cn skyline account for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete 5t skyline account from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            account = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        account.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"cn_account": self.kwargs["pk"], "message": "Successfully Deleted"})
