"""
    Title: Account Tier Api views
    Description: This file will contain all functions for account tier api functions.
    Created: February 15, 2021
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
from api.models import AccountTier
from api.serializers_v3.private.account.tier_serializers import PrivateTierSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class AccountTierApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    # Customs
    _cache_lookup_key = "tiers"

    def get_queryset(self):
        """
            Get initial account tier queryset and apply query params to the queryset.
            :return:
        """

        tiers = cache.get(self._cache_lookup_key)

        if not tiers:
            tiers = AccountTier.objects.all()
            cache.set(self._cache_lookup_key, tiers, TWENTY_FOUR_HOURS_CACHE_TTL)

        return tiers

    @swagger_auto_schema(
        operation_id='Get Tiers',
        operation_description='Get a list of tiers which contains information including name, restrictions '
                              'and permissions.',
        responses={
            '200': openapi.Response('Get Tiers', PrivateTierSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get account tier for the system based on the allowed parameters and search params.
            :return:
        """

        tiers = self.get_queryset()
        tiers = self.filter_queryset(queryset=tiers)
        serializer = PrivateTierSerializer(tiers, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateTierSerializer,
        operation_id='Create Tier',
        operation_description='Create a Tier which contains information including name, restrictions, and permissions',
        responses={
            '200': openapi.Response('Create Tier', PrivateTierSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new tier.
            :param request: request
            :return: Json list of tier.
        """
        errors = []

        json_data = request.data
        serializer = PrivateTierSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="7800", message="Tier: Invalid values.", errors=serializer.errors
            )

        try:
            tier = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="7801", message="Tier: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = tier
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class AccountTierDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "tiers"
    _cache_lookup_key_individual = "tiers_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = AccountTier.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"tier": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="7802", message="Tier: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Tier',
        operation_description='Get a tier which contains information including name, restrictions and permissions.',
        responses={
            '200': openapi.Response('Get Tier', PrivateTierSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get tier information.
            :return: Json of tier.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_airports = cache.get(lookup_key)

        if not cached_airports:

            try:
                tier = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateTierSerializer(instance=tier, many=False)
            cached_airports = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_airports, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_airports)

    @swagger_auto_schema(
        request_body=PrivateTierSerializer,
        operation_id='Update Tier',
        operation_description='Update a tier information including name, restrictions and permissions.',
        responses={
            '200': openapi.Response('Update Tier', PrivateTierSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update tier information
            :param request: request
            :return: Json of tier.
        """
        errors = []
        json_data = request.data
        serializer = PrivateTierSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="7803", message="Tier: Invalid values.", errors=serializer.errors
            )

        try:
            tier = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            tier = serializer.update(instance=tier, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="7804", message="Tier: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = tier
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Tier',
        operation_description='Delete a tier from the system.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete tier from the system.
            :param request: request
            :return: Success tier.
        """

        try:
            tier = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        tier.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"tier": self.kwargs["pk"], "message": "Successfully Deleted"})
