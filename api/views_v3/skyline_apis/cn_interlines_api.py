"""
    Title: 5T Interline Api
    Description: This file will contain all functions for 5T Interline apis.
    Created: February 04, 2021
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
from api.models import CNInterline
from api.serializers_v3.private.cn.interline_serializers import PrivateInterlineSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CNInterlineApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['origin', 'destination', 'interline_id', 'interline_carrier']

    # Customs
    _cache_lookup_key = "cn_interline"

    def get_queryset(self):
        """
            Get initial 5t Interline queryset and apply query params to the queryset.
            :return:
        """

        interlines = cache.get(self._cache_lookup_key)

        if not interlines:
            interlines = CNInterline.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, interlines, TWENTY_FOUR_HOURS_CACHE_TTL)

        return interlines

    @swagger_auto_schema(
        operation_id='Get CN Interline lanes',
        operation_description='Get a list of canadian north interline lanes which includes which carrier it is.',
        responses={
            '200': openapi.Response('Get CN Interline lanes', PrivateInterlineSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get Interlines based on the allowed parameters and search params.
            :return:
        """

        interlines = self.get_queryset()
        interlines = self.filter_queryset(queryset=interlines)
        serializer = PrivateInterlineSerializer(interlines, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateInterlineSerializer,
        operation_id='Create CN Interline lane',
        operation_description='Create a cn interline lane which includes which carrier it is.',
        responses={
            '200': openapi.Response('Create CN Interline lane', PrivateInterlineSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new 5t Interline.
            :param request: request
            :return: 5t Interline json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateInterlineSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6100", message="CN Interline: Invalid values.", errors=serializer.errors
            )

        try:
            interline = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6101", message="CN Interline: Failed to save.", errors=errors)
        except ViewException as e:
            errors.append({"cn_interline": e.message})
            return Utility.json_error_response(code="6102", message="CN Interline: Failed to save.", errors=errors)

        serializer.instance = interline
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class CNInterlineDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "cn_interline"
    _cache_lookup_key_individual = "cn_interline_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = CNInterline.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"cn_interline": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="6101", message="CN Interline: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get CN Interline lane',
        operation_description='Get a canadian north interline lane which includes which carrier it is.',
        responses={
            '200': openapi.Response('Get CN Interline lane', PrivateInterlineSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get 5t nInterline information.
            :return: Json of 5t Interline
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_pd = cache.get(lookup_key)

        if not cached_pd:

            try:
                interline = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateInterlineSerializer(instance=interline, many=False)
            cached_pd = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_pd, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_pd)

    @swagger_auto_schema(
        request_body=PrivateInterlineSerializer,
        operation_id='Update CN Interline lane',
        operation_description='Update a canadian north interline lane which includes which carrier it is.',
        responses={
            '200': openapi.Response('Update CN Interline lane', PrivateInterlineSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update 5t Interline information
            :param request: request
            :return: Json of 5t Interline.
        """
        errors = []
        json_data = request.data
        serializer = PrivateInterlineSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6104", message="CN Interline: Invalid values.", errors=serializer.errors
            )

        try:
            interline = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            interline = serializer.update(instance=interline, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6106", message="CN Interline: Failed to update.", errors=errors)
        except ViewException as e:
            errors.append({"cn_interline": e.message})
            return Utility.json_error_response(code="6107", message="CN Interline: Failed to update.", errors=errors)

        serializer.instance = interline
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete CN Interline lane',
        operation_description='Delete an cn interline lane for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete 5t Interline from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            interline = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        interline.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"cn_interline": self.kwargs["pk"], "message": "Successfully Deleted"})
