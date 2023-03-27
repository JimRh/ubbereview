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
from rest_framework.generics import ListCreateAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import CarrierOption
from api.serializers_v3.private.options.optional_option_serializers import OptionalOptionsSerializer, \
    CreateOptionalOptionsSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class OptionalOptionApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post', 'put', 'delete']

    # Customs
    _cache_lookup_key = "optional_options"

    def get_queryset(self):
        """
            Get Optional Option queryset and apply query params to the queryset.
            :return:
        """

        options = cache.get(self._cache_lookup_key)

        if not options:
            options = CarrierOption.objects.select_related("carrier", "option").all()

            # Store metrics for 24 hours
            cache.set(self._cache_lookup_key, options, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'carrier_code' in self.request.query_params:
            options = options.filter(carrier__code=self.request.query_params["carrier_code"])

        return options

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
            )
        ],
        operation_id='Get Optional Options',
        operation_description='Get a list of optional options for all carriers. Optional parameter of carrier_code '
                              'to filter the options down to the carrier.',
        responses={
            '200': openapi.Response('Get Optional Options', OptionalOptionsSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get option names that are in the system.
            :return:
        """

        options = self.get_queryset()
        serializer = OptionalOptionsSerializer(options, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=CreateOptionalOptionsSerializer,
        operation_id='Create Optional Option',
        operation_description='Create a optional option.',
        responses={
            '200': openapi.Response('Create Optional Option', OptionalOptionsSerializer),
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
        serializer = CreateOptionalOptionsSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2500", message="Optional Options: Invalid values.", errors=serializer.errors
            )

        try:
            option = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2501", message="Optional Options: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        response_optional = OptionalOptionsSerializer(instance=option, many=False)
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=response_optional.data)

    @swagger_auto_schema(
        request_body=OptionalOptionsSerializer,
        operation_id='Update Optional Option',
        operation_description='Update a optional option information',
        responses={
            '200': openapi.Response('Update Optional Option', OptionalOptionsSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Optional Option information.
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        serializer = OptionalOptionsSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2502", message="Optional Options: Invalid values.", errors=serializer.errors
            )

        try:
            option_name = CarrierOption.objects.get(id=int(json_data.get("id", -1)))
        except ObjectDoesNotExist:
            errors.append({"optional_option": f'{json_data.get("id", -1)} not found or you do not have permission.'})
            return Utility.json_error_response(code="2503", message="Optional Options: Not Found.", errors=errors)

        try:
            option = serializer.update(instance=option_name, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2504", message="Optional Option: Failed to update.", errors=errors)

        serializer.instance = option
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Optional option',
        operation_description='Delete an optional option for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete optional option from the system.
            :param request: request
            :return: Success Message.
        """
        errors = []
        json_data = request.data

        try:
            option = CarrierOption.objects.get(id=int(json_data.get("id", -1)))
        except ObjectDoesNotExist:
            errors.append({"optional_option": f'{json_data.get("id", -1)} not found or you do not have permission.'})
            return Utility.json_error_response(code="2503", message="Optional Options: Not Found.", errors=errors)

        option.delete()
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data={"option": json_data.get("id", -1), "message": "Successfully Deleted"})
