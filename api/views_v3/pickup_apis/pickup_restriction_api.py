"""
    Title: Pickup Restriction Api
    Description: This file will contain all functions for pickup restriction apis.
    Created: November 17, 2021
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
from api.models import CarrierPickupRestriction
from api.serializers_v3.common.pickup_restriction_serializers import PickupRestrictionSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class PickupRestrictionApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']

    # Customs
    _cache_lookup_key = "pickup_restrictions"

    def get_queryset(self):
        """
            Get initial pickup restriction queryset and apply query params to the queryset.
            :return:
        """

        restrictions = cache.get(self._cache_lookup_key)

        if not restrictions:
            restrictions = CarrierPickupRestriction.objects.select_related("carrier").all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, restrictions, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'carrier_code' in self.request.query_params:
            restrictions = restrictions.filter(carrier__code=self.request.query_params["carrier_code"])

        return restrictions

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER,
            )
        ],
        operation_id='Get Pickup Restrictions',
        operation_description='Get a list of pickup restrictions for all carriers.',
        responses={
            '200': openapi.Response('Get Pickup Restrictions', PickupRestrictionSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get pickup restrictions based on the allowed parameters and search paramms.
            :return:
        """

        restrictions = self.get_queryset()
        serializer = PickupRestrictionSerializer(restrictions, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PickupRestrictionSerializer,
        operation_id='Create Pickup Restriction',
        operation_description='Create a pickup restriction that contains information about pickup requirements to '
                              'meet in order for the carrier to pickup.',
        responses={
            '200': openapi.Response('Create Pickup Restriction', PickupRestrictionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new Pickup Restriction.
            :param request: request
            :return: Pickup Restriction json.
        """
        errors = []
        json_data = request.data
        serializer = PickupRestrictionSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2300", message="Pickup Restrictions: Invalid values.", errors=serializer.errors
            )

        if CarrierPickupRestriction.objects.filter(carrier__code=json_data["carrier_code"]).exists():
            errors.append({"pickup_restriction": f'Pickup Restriction already exists for carrier.'})
            return Utility.json_error_response(
                code="2301", message="Pickup Restrictions: Already Exists.", errors=errors
            )

        try:
            restriction = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(
                code="2302", message="Pickup Restrictions: Failed to save.", errors=errors
            )
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = restriction
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class PickupRestrictionDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "pickup_restrictions"
    _cache_lookup_key_individual = "pickup_restrictions_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = CarrierPickupRestriction.objects.select_related("carrier").get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"pickup_restriction": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="2304", message="Pickup Restrictions: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Pickup Restriction',
        operation_description='Get pickup restriction for carrier to see requirements for pickup.',
        responses={
            '200': openapi.Response('Get Pickup Restriction', PickupRestrictionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get pickup restriction information.
            :return: Json of pickup restriction.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_restriction = cache.get(lookup_key)

        if not cached_restriction:

            try:
                restriction = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PickupRestrictionSerializer(instance=restriction, many=False)
            cached_restriction = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_restriction, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_restriction)

    @swagger_auto_schema(
        request_body=PickupRestrictionSerializer,
        operation_id='Update Pickup Restriction',
        operation_description='Update pickup restriction for carrier.',
        responses={
            '200': openapi.Response('Update Pickup Restriction', PickupRestrictionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update pickup restriction information
            :param request: request
            :return: Json of pickup restriction.
        """
        errors = []
        json_data = request.data
        serializer = PickupRestrictionSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2305", message="Pickup Restrictions: Invalid values.", errors=serializer.errors
            )

        try:
            restriction = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            restriction = serializer.update(instance=restriction, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(
                code="2307", message="Pickup Restrictions: failed to update.", errors=errors
            )
        except ViewException as e:
            errors.append({"pickup_restriction": e.message})
            return Utility.json_error_response(
                code="2308", message="Pickup Restrictions: failed to update.", errors=errors
            )

        serializer.instance = restriction
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Pickup Restriction',
        operation_description='Delete an pickup restriction for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete pickup restriction from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            restriction = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        restriction.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={
            "pickup_restriction": self.kwargs["pk"], "message": "Successfully Deleted"
        })
