"""
    Title: Options Api Views V3
    Description: This file will contain all api views for Options.
    Created: Nov 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import OptionName
from api.serializers_v3.common.option_serializers import OptionsSerializer, OptionNameSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class OptionsApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    # Customs
    _cache_lookup_key = "options_public"
    _sub_account = None

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        options = cache.get(self._cache_lookup_key)

        if not options:
            options = OptionName.objects.prefetch_related("carrier_option_option__carrier").filter(is_mandatory=False)

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, options, TWENTY_FOUR_HOURS_CACHE_TTL)

        return options

    @swagger_auto_schema(
        operation_id='Get Options',
        operation_description='Get a list of supported options in ubbe. Note: Not all carriers support them, '
                              'somme options will eliminate carriers.',
        responses={
            '200': openapi.Response('Get Options', OptionsSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get all optional Options to be used for ubbe shipping process.
            :return:
        """

        options = self.get_queryset()
        serializer = OptionsSerializer(options, many=True)

        return Utility.json_response(data=serializer.data)


class OptionNameApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'post', 'put', 'delete']

    # Customs
    _cache_lookup_key = "options"
    _cache_lookup_key_other = "options_public"
    _sub_account = None

    @swagger_auto_schema(
        operation_id='Get Option Names',
        operation_description='Get a list of supported options in ubbe.',
        responses={
            '200': openapi.Response('Get Option Names', OptionNameSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get option names that are in the system.
            :return:
        """

        options = cache.get(self._cache_lookup_key)

        if not options:
            options = OptionName.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, options, TWENTY_FOUR_HOURS_CACHE_TTL)

        serializer = OptionNameSerializer(options, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=OptionNameSerializer,
        operation_id='Create Option Name',
        operation_description='Create a option name to support.',
        responses={
            '200': openapi.Response('Create Option Name', OptionNameSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new option name.
            :param request: request
            :return: Json of option name.
        """
        errors = []
        json_data = request.data
        serializer = OptionNameSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2400", message="Options: Invalid values.", errors=serializer.errors
            )

        try:
            option = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2401", message="Option: failed to save.", errors=errors)

        serializer.instance = option
        cache.delete(self._cache_lookup_key)
        cache.delete(self._cache_lookup_key_other)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=OptionNameSerializer,
        operation_id='Update Option Name',
        operation_description='Update a option name information',
        responses={
            '200': openapi.Response('Update Option Name', OptionNameSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Option Name
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        serializer = OptionNameSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2402", message="Options: Invalid values.", errors=serializer.errors
            )

        try:
            option_name = OptionName.objects.get(id=int(json_data.get("id", -1)))
        except ObjectDoesNotExist:
            errors.append({"option": f'{self.kwargs["id"]} not found or you do not have permission.'})
            return Utility.json_error_response(code="2403", message="Option: Not Found.", errors=errors)

        try:
            option = serializer.update(instance=option_name, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2404", message="Option: failed to update.", errors=errors)

        serializer.instance = option
        cache.delete(self._cache_lookup_key)
        cache.delete(self._cache_lookup_key_other)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Option Name',
        operation_description='Delete an option name and all mandatory and optional options.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete option name and all related Optional and Mandatory carrier options from the system.
            :param request: request
            :return: Success Message.
        """
        errors = []
        json_data = request.data

        try:
            option_name = OptionName.objects.get(id=int(json_data.get("id", -1)))
        except ObjectDoesNotExist:
            errors.append({"option": f'{self.kwargs["id"]} not found or you do not have permission.'})
            return Utility.json_error_response(code="2405", message="Option: Not Found.", errors=errors)

        option_name.carrier_option_option.all().delete()
        option_name.mandatory_option_option.all().delete()
        option_name.delete()

        cache.delete(self._cache_lookup_key)
        cache.delete(self._cache_lookup_key_other)

        return Utility.json_response(data={"option": json_data["id"], "message": "Successfully Deleted"})
