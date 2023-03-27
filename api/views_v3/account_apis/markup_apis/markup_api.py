"""
    Title: Markup api views
    Description: This file will contain all functions for markup serializers.
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
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Markup, MarkupHistory
from api.serializers_v3.private.account.markup_history_serializers import PrivateMarkupHistorySerializer
from api.serializers_v3.private.account.markup_serializers import PrivateMarkupSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class MarkupApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    # Customs
    _cache_lookup_key = "markups"

    def get_queryset(self):
        """
            Get initial markup queryset and apply query params to the queryset.
            :return:
        """

        data = cache.get(self._cache_lookup_key)

        if not data:
            data = Markup.objects.all()

            # Store metrics for 24 hours
            cache.set(self._cache_lookup_key, data, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'is_template' in self.request.query_params:
            data = data.filter(is_template=self.request.query_params["is_template"])

        return data

    @swagger_auto_schema(
        operation_id='Get Markups',
        operation_description='Get a list of markups in the system which contains the default percentage to set new '
                              'carriers to.',
        responses={
            '200': openapi.Response('Get Markups', PrivateMarkupSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get markups for the system based on the allowed parameters and search params.
            :return:
        """

        markups = self.get_queryset()
        markups = self.filter_queryset(queryset=markups)
        serializer = PrivateMarkupSerializer(markups, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateMarkupSerializer,
        operation_id='Create Markup',
        operation_description='Create a markup which will also create all the related carrier markups.',
        responses={
            '200': openapi.Response('Create Markup', PrivateMarkupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new markup.
            :param request: request
            :return: Json list of markups.
        """
        errors = []
        json_data = request.data
        serializer = PrivateMarkupSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3700", message="Markup: Invalid values.", errors=serializer.errors
            )

        try:
            markup = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3701", message="Markup: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = markup
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class MarkupDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "markups"
    _cache_lookup_key_individual = "markups_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Markup.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Markup',
        operation_description='Get a markup in the system which contains the default percentage to set '
                              'new carriers to.',
        responses={
            '200': openapi.Response('Get Markup', PrivateMarkupSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get markup information.
            :return: Json of markup.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_markup = cache.get(lookup_key)

        if not cached_markup:

            try:
                markup = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateMarkupSerializer(instance=markup, many=False)
            cached_markup = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_markup, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_markup)

    @swagger_auto_schema(
        request_body=PrivateMarkupSerializer,
        operation_id='Update Markup',
        operation_description='Update a markup which contains the default carrier percentage and name.',
        responses={
            '200': openapi.Response('Create Markup', PrivateMarkupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update markup information
            :param request: request
            :return: Json of markup.
        """
        errors = []
        json_data = request.data
        serializer = PrivateMarkupSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3704", message="Markup: Invalid values.", errors=serializer.errors
            )

        try:
            markup = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.validated_data["username"] = request.user.username

        try:
            markup = serializer.update(instance=markup, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3706", message="Markup: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = markup
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Markup',
        operation_description='Delete a markup for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete markup from the system.
            :param request: request
            :return: Success markup.
        """

        try:
            markup = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        markup.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"markup": self.kwargs["pk"], "message": "Successfully Deleted"})


class MarkupHistoryApi(UbbeMixin, ListAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial markup history queryset and apply query params to the queryset.
            :return:
        """
        return MarkupHistory.objects.filter(markup__id=self.kwargs["pk"])

    @swagger_auto_schema(
        operation_id='Get Markup Histories',
        operation_description='Get a markup histories for a markup which contains all changes that occurred and who '
                              'changed made the change.',
        responses={
            '200': openapi.Response('Get Markup Histories', PrivateMarkupHistorySerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get markup history for the system based on the allowed parameters and search params.
            :return:
        """

        histories = self.get_queryset()
        serializer = PrivateMarkupHistorySerializer(histories, many=True)

        return Utility.json_response(data=serializer.data)
