"""
    Title: Saved Broker api views
    Description: This file will contain all functions for saved broker api functions.
    Created: May 10, 2022
    Author: Yusuf Abdulla
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
from api.models import SavedBroker
from api.serializers_v3.common.saved_broker_serializer import SavedBrokerSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class SavedBrokerApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['sub_account__subaccount_name', 'sub_account__subaccount_number', 'address', 'contact']

    # Customs
    _cache_lookup_key = "saved_broker"

    def get_queryset(self):
        """
            Get initial saved broker queryset and apply query params to the queryset.
            :return:
        """

        hooks = cache.get(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")

        if not hooks:
            hooks = SavedBroker.objects.select_related(
                "sub_account__contact",
                "address__province__country",
                "contact"
            ).filter(sub_account=self._sub_account)

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, hooks, FIVE_HOURS_CACHE_TTL)

        return hooks

    @swagger_auto_schema(
        operation_id='Get Saved Broker',
        operation_description='Get a list of saved brokers available in the system.',

        responses={
            '200': openapi.Response('Get Saved Broker', SavedBrokerSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get saved brokers for the system based on the allowed parameters and search params.
            :return:
        """

        hooks = self.get_queryset()
        hooks = self.filter_queryset(queryset=hooks)
        serializer = SavedBrokerSerializer(hooks, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=SavedBrokerSerializer,
        operation_id='Create Saved Broker',
        operation_description='Create a saved broker for the system.',
        responses={
            '200': openapi.Response('Create Saved Broker', SavedBrokerSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new saved brokers.
            :param request: request
            :return: Json of saved brokers.
        """
        errors = []
        json_data = request.data
        serializer = SavedBrokerSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1200", message="Saved Broker: Invalid values.", errors=serializer.errors
            )

        try:
            hook = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1201", message="Saved Broker: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = hook
        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")

        return Utility.json_response(data=serializer.data)


class SavedBrokerDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "saved_broker"
    _cache_lookup_key_individual = "saved_broker_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = SavedBroker.objects.select_related("sub_account").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"broker": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1103", message="Saved Broker: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Saved Broker',
        operation_description='Get a saved broker available in the system.',
        responses={
            '200': openapi.Response('Get Saved Broker', SavedBrokerSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get saved broker information.
            :return: Json of saved broker.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_hook = cache.get(lookup_key)

        if not cached_hook:

            try:
                hook = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = SavedBrokerSerializer(instance=hook, many=False)
            cached_hook = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_hook, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_hook)

    @swagger_auto_schema(
        request_body=SavedBrokerSerializer,
        operation_id='Update Saved Broker',
        operation_description='Update a saved broker in the system.',
        responses={
            '200': openapi.Response('Update Saved Broker', SavedBrokerSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Saved Broker information
            :param request: request
            :return: Json of web hook.
        """
        errors = []
        json_data = request.data
        serializer = SavedBrokerSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1204", message="Saved Broker: Invalid values.", errors=serializer.errors
            )

        try:
            hook = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            hook = serializer.update(instance=hook, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1206", message="Saved Broker: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = hook
        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Saved Broker',
        operation_description='Delete a saved broker for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete saved broker from the system.
            :param request: request
            :return: Success message.
        """

        try:
            hook = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        hook.delete()
        cache.delete(f"{self._cache_lookup_key}_{self._sub_account.subaccount_number}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"SavedBroker": self.kwargs["pk"], "message": "Successfully Deleted"})
