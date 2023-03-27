"""
    Title: Webhook api views
    Description: This file will contain all functions for webhook api functions.
    Created: November 23, 2021
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
from api.models import Webhook
from api.serializers_v3.common.webhook_serializers import WebhookSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class WebhookApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['event', 'sub_account__system', 'sub_account__subaccount_number', 'data_format']

    # Customs
    _cache_lookup_key = "webhook"

    def get_queryset(self):
        """
            Get initial webhooks queryset and apply query params to the queryset.
            :return:
        """

        hooks = cache.get(self._cache_lookup_key)

        if not hooks:
            hooks = Webhook.objects.select_related("sub_account").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, hooks, FIVE_HOURS_CACHE_TTL)

        if not self._sub_account.is_bbe:
            hooks = hooks.filter(sub_account=self._sub_account)

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            hooks = hooks.filter(sub_account__subaccount_number=self.request.query_params["account"])

        if 'event' in self.request.query_params:
            hooks = hooks.filter(event=self.request.query_params["event"])

        if 'data_format' in self.request.query_params:
            hooks = hooks.filter(data_format=self.request.query_params["data_format"])

        return hooks

    @swagger_auto_schema(
        operation_id='Get Webhooks',
        operation_description='Get a list of webhooks available in the system.',
        manual_parameters=[
            openapi.Parameter(
                'event', openapi.IN_QUERY, description="Event filter", type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'data_format', openapi.IN_QUERY, description="Json (JSO) - xml (XML)", type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            '200': openapi.Response('Get Webhooks', WebhookSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get webhooks for the system based on the allowed parameters and search params.
            :return:
        """

        hooks = self.get_queryset()
        hooks = self.filter_queryset(queryset=hooks)
        serializer = WebhookSerializer(hooks, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=WebhookSerializer,
        operation_id='Create Webhook',
        operation_description='Create a webhook for the system.',
        responses={
            '200': openapi.Response('Create Webhook', WebhookSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new webhooks.
            :param request: request
            :return: Json of web hooks.
        """
        errors = []
        json_data = request.data
        serializer = WebhookSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1200", message="Webhook: Invalid values.", errors=serializer.errors
            )

        try:
            hook = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1201", message="Webhook: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = hook
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class WebhookDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "webhook"
    _cache_lookup_key_individual = "webhook_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Webhook.objects.select_related("sub_account").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"webhook": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1103", message="Package Type: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Webhook',
        operation_description='Get a webhook available in the system.',
        responses={
            '200': openapi.Response('Get Webhooks', WebhookSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get web hook information.
            :return: Json of web hook.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_hook = cache.get(lookup_key)

        if not cached_hook:

            try:
                hook = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = WebhookSerializer(instance=hook, many=False)
            cached_hook = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_hook, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_hook)

    @swagger_auto_schema(
        request_body=WebhookSerializer,
        operation_id='Update Webhook',
        operation_description='Update a webhook in the system.',
        responses={
            '200': openapi.Response('Update Webhook', WebhookSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update web hook information
            :param request: request
            :return: Json of web hook.
        """
        errors = []
        json_data = request.data
        serializer = WebhookSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1204", message="Webhook: Invalid values.", errors=serializer.errors
            )

        try:
            hook = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            hook = serializer.update(instance=hook, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1206", message="Webhook: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = hook
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Webhook',
        operation_description='Delete an webhook for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete web hook from the system.
            :param request: request
            :return: Success message.
        """

        try:
            hook = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        hook.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"webhook": self.kwargs["pk"], "message": "Successfully Deleted"})
