"""
    Title: Mandatory Options Api Views V3
    Description: This file will contain all api views for Mandatory Options.
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
from api.models import MandatoryOption
from api.serializers_v3.private.options.mandatory_option_serializers import MandatoryOptionsSerializer, \
    CreateMandatoryOptionsSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class MandatoryOptionApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post', 'put', 'delete']

    # Customs
    _cache_lookup_key = "mandatory_options"

    def get_queryset(self):
        """
            Get Mandatory Option queryset and apply query params to the queryset.
            :return:
        """

        options = cache.get(self._cache_lookup_key)

        if not options:
            options = MandatoryOption.objects.select_related("carrier", "option").all()

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
        operation_id='Get Mandatory Options',
        operation_description='Get a list of mandatory options for all carriers. Optional parameter of carrier_code '
                              'to filter the options down to the carrier.',
        responses={
            '200': openapi.Response('Get Mandatory Options', MandatoryOptionsSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get mandatory option that are in the system.
            :return:
        """

        options = self.get_queryset()
        serializer = MandatoryOptionsSerializer(options, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=CreateMandatoryOptionsSerializer,
        operation_id='Create Mandatory Option',
        operation_description='Create a mandatory option.',
        responses={
            '200': openapi.Response('Create Mandatory Option', MandatoryOptionsSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new mandatory option.
            :param request: request
            :return: Json of mandatory option.
        """
        errors = []
        json_data = request.data
        serializer = CreateMandatoryOptionsSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2600", message="Mandatory Options: Invalid values.", errors=serializer.errors
            )

        try:
            option = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2601", message="Mandatory Option: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        response_optional = MandatoryOptionsSerializer(instance=option, many=False)
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=response_optional.data)

    @swagger_auto_schema(
        request_body=MandatoryOptionsSerializer,
        operation_id='Update Mandatory Option',
        operation_description='Update a mandatory option information',
        responses={
            '200': openapi.Response('Update Mandatory Option', MandatoryOptionsSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update mandatory option
            :param request: request
            :return: Json of mandatory option.
        """
        errors = []
        json_data = request.data
        serializer = MandatoryOptionsSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2602", message="Mandatory Options: Invalid values.", errors=serializer.errors
            )

        try:
            option_name = MandatoryOption.objects.get(id=int(json_data.get("id", -1)))
        except ObjectDoesNotExist:
            errors.append({"mandatory_option": f'{json_data.get("id", -1)} not found or you do not have permission.'})
            return Utility.json_error_response(code="2603", message="Mandatory Options: Not Found.", errors=errors)

        try:
            option = serializer.update(instance=option_name, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="2604", message="Mandatory Option Failed to update.", errors=errors)

        serializer.instance = option
        cache.delete(self._cache_lookup_key)
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Mandatory option',
        operation_description='Delete an mandatory option for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete Mandatory options from the system.
            :param request: request
            :return: Success Message.
        """
        errors = []
        json_data = request.data

        try:
            option = MandatoryOption.objects.get(id=int(json_data.get("id", -1)))
        except ObjectDoesNotExist:
            errors.append({"mandatory_option": f'{json_data.get("id", -1)} not found or you do not have permission.'})
            return Utility.json_error_response(code="2603", message="Mandatory Options: Not Found.", errors=errors)

        option.delete()
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data={"option": json_data.get("id", -1), "message": "Successfully Deleted"})
