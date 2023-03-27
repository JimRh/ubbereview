"""
    Title: Fuel Surcharge Serializers
    Description: This file will contain all functions for Fuel Surcharge serializers.
    Created: November 15, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import FuelSurcharge
from api.serializers_v3.private.carriers.fuel_surcharge_serializers import PrivateFuelSurchargeSerializer, \
    PrivateCreateFuelSurchargeSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class FuelSurchargeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']

    # Customs
    _cache_lookup_key = "fuel_surcharges"

    def get_queryset(self):
        """
            Get initial fuel surcharge queryset and apply query params to the queryset.
            :return:
        """

        fuels = cache.get(self._cache_lookup_key)

        if not fuels:
            fuels = FuelSurcharge.objects.select_related("carrier").all().order_by("-updated_date")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, fuels, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'code' in self.request.query_params:
            fuels = fuels.filter(carrier__code=self.request.query_params["code"])

        if 'fuel_type' in self.request.query_params:
            fuels = fuels.filter(fuel_type=self.request.query_params["fuel_type"])

        return fuels

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'fuel_type', openapi.IN_QUERY, description="Domestic (D) or International (I)", type=openapi.TYPE_STRING
            )
        ],
        operation_id='Get Fuel Surcharges',
        operation_description='Get a list of fuel surcharges that is used for rate sheet carriers and contain the '
                              'traditional three break points for weight. These are updated every monday.',
        responses={
            '200': openapi.Response('Get Fuel Surcharges', PrivateFuelSurchargeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get fuel surcharges levels based on the allowed parameters and search params.
            :return:
        """

        fuel_surcharges = self.get_queryset()
        serializer = PrivateFuelSurchargeSerializer(fuel_surcharges, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateFuelSurchargeSerializer,
        operation_id='Create Fuel Surcharge',
        operation_description='Create a fuel surcharge with percentages for each weight break, also include updated '
                              'date.',
        responses={
            '200': openapi.Response('Create Fuel Surcharge', PrivateFuelSurchargeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new fuel surcharge.
            :param request: request
            :return: json of fuel surcharge.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateFuelSurchargeSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1700", message="Fuel Surcharge: Invalid values.", errors=serializer.errors
            )

        try:
            service = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1701", message="Fuel Surcharge: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateFuelSurchargeSerializer(instance=service, many=False)
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class FuelSurchargeDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "fuel_surcharges"
    _cache_lookup_key_individual = "fuel_surcharge_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = FuelSurcharge.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"fuel_surcharge": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1703", message="Fuel Surcharge: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Fuel Surcharge',
        operation_description='Get a fuel surcharge that is used for rate sheet carriers and contain the '
                              'traditional three break points for weight. These are updated very monday.',
        responses={
            '200': openapi.Response('Get Fuel Surcharge', PrivateFuelSurchargeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get fuel surcharge information.
            :return: Json of fuel surcharge.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_fuel = cache.get(lookup_key)

        if not cached_fuel:

            try:
                fuel = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateFuelSurchargeSerializer(instance=fuel, many=False)
            cached_fuel = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_fuel, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_fuel)

    @swagger_auto_schema(
        request_body=PrivateFuelSurchargeSerializer,
        operation_id='Update Fuel Surcharge',
        operation_description='Update an fuel surcharge weight breaks with new percentages to be used, also include '
                              'updated date.',
        responses={
            '200': openapi.Response('Update Bill of Lading', PrivateFuelSurchargeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update fuel surcharge information
            :param request: request
            :return: Json of fuel surcharge
        """
        errors = []
        json_data = request.data
        serializer = PrivateFuelSurchargeSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1704", message="Fuel Surcharge: Invalid values.", errors=serializer.errors
            )

        try:
            fuel = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            fuel = serializer.update(instance=fuel, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1706", message="Fuel Surcharge: Failed to update.", errors=errors)

        serializer.instance = fuel
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Fuel Surcharge',
        operation_description='Delete an fuel surcharge for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete fuel surcharge from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            fuel = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        fuel.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"fuel_surcharge": self.kwargs["pk"], "message": "Successfully Deleted"})
