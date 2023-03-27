"""
    Title: Pickup Apis
    Description: This file will contain api eendpoints that relate to carrier pickups requests or validating pickup
                details for the request.
    Created: November 17, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

import pytz
from django.core.cache import cache
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

from rest_framework.views import APIView

from api.apis.pickup.pickup import Pickup
from api.apis.pickup.pickup_validate import PickupValidate
from api.exceptions.project import PickupException, ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import CarrierPickupRestriction, City
from api.serializers_v3.common.timezone_serializer import CityTimezoneSerializer
from api.serializers_v3.common.pickup_validate_serializers import PickupValidateSerializer
from api.serializers_v3.common.pickup_restriction_serializers import PickupRestrictionSerializer
from api.serializers_v3.public.pickup_serializer import PickupSerializer, CancelPickupSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class PickupApi(UbbeMixin, APIView):
    http_method_names = ['post', 'put', 'delete']

    @swagger_auto_schema(
        request_body=PickupSerializer,
        operation_id='Create Pickup',
        operation_description='Create a pickup for a shipment leg.',
        responses={
            '200': openapi.Response('Create Pickup', PickupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new Pickup.
            :param request: request
            :return: Pickup json.
        """

        json_data = request.data
        serializer = PickupSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="", message="Pickup: Invalid values.", errors=serializer.errors
            )

        try:
            pickup = serializer.create(validated_data=serializer.validated_data)
        except serializers.ValidationError as e:
            return Utility.json_error_response(
                code="2302", message="Pickup: Failed to save.", errors=e.detail
            )
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=pickup)

    @swagger_auto_schema(
        request_body=PickupSerializer,
        operation_id='Create Pickup',
        operation_description='Create a pickup for a shipment leg.',
        responses={
            '200': openapi.Response('Create Pickup', PickupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update a Pickup.
            :param request: request
            :return: Pickup json.
        """

        json_data = request.data
        serializer = PickupSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="", message="Pickup: Invalid values.", errors=serializer.errors
            )

        try:
            pickup = serializer.update(validated_data=serializer.validated_data, instance=None)
        except serializers.ValidationError as e:
            return Utility.json_error_response(
                code="2302", message="Pickup: Failed to save.", errors=e.detail
            )
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=pickup)

    @swagger_auto_schema(
        request_body=CancelPickupSerializer,
        operation_id='Cancel Pickup',
        operation_description='Cancel an pickup for a shipment leg.',
        responses={
            '200': "Successfully Canceled",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
        Cancel Pickup for a shipment leg.
        :param request: request
        :return: Success Message.
        """

        serializer = CancelPickupSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="", message="Pickup: Invalid values.", errors=serializer.errors
            )

        try:
            ret = Pickup(ubbe_request=serializer.validated_data).cancel()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=ret)


class PickupTimezoneApi(UbbeMixin, APIView):

    # Customs
    _cache_lookup_key = "timezone"

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'city', openapi.IN_QUERY, description="City Name", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'province', openapi.IN_QUERY, description="Province Code", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'country', openapi.IN_QUERY, description="Country Code", type=openapi.TYPE_STRING, required=True
            )
        ],
        operation_id='Get Timezone',
        operation_description='Get timezone information for a city, province, coountry combination.',
        responses={
            '200': openapi.Response('Get Timezone', CityTimezoneSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get timezone for city.
            :param request: request
            :return: city timezone.
        """
        errors = []
        city = self.request.query_params.get("city")
        province = self.request.query_params.get("province")
        country = self.request.query_params.get("country")

        if not city:
            errors.append({"city": "The param: 'city' is a mandatory field."})
            return Utility.json_error_response(
                code="800", message="Pickup Timezone: The param: 'city' is a mandatory field.", errors=errors
            )

        if not province:
            errors.append({"province": "The param: 'province' is a mandatory field."})
            return Utility.json_error_response(
                code="801", message="Pickup Timezone: The param: 'province' is a mandatory field.", errors=errors
            )

        if not country:
            errors.append({"country": "The param: 'country' is a mandatory field."})
            return Utility.json_error_response(
                code="802", message="Pickup Timezone: The param: 'country' is a mandatory field.", errors=errors
            )

        look_up = f"{self._cache_lookup_key}_{city.lower()}_{province.lower()}_{country.lower()}"
        data = cache.get(look_up)

        if not data:
            try:
                city = City().get_timezone(name=city, province=province, country=country, is_object=True)
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = CityTimezoneSerializer(city, many=False)
            data = serializer.data

            # Store metrics for 5 hours
            cache.set(look_up, data, TWENTY_FOUR_HOURS_CACHE_TTL)

        data["timezone_time"] = datetime.datetime.now(tz=pytz.timezone(data["timezone"])).strftime("%Y-%m-%d %H:%M")

        return Utility.json_response(data=data)


class PickupValidateApi(UbbeMixin, APIView):
    http_method_names = ['get', 'post']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'carrier_ids', openapi.IN_QUERY,
                description="Carrier Code",
                type=openapi.TYPE_ARRAY,
                required=True,
                items=openapi.Items(type=openapi.TYPE_INTEGER)
            )
        ],
        operation_id='Get Carrier Pickup Restrictions',
        operation_description='Get pickup restrictions for a list of carriers.',
        responses={
            '200': openapi.Response('Get Pickup Restrictions', PickupRestrictionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get all Carrier Pickup Restriction in ubbe.
            :param request: request
            :return: Json list of Carrier Pickup Restriction.
        """
        errors = []
        carrier_ids = self.request.query_params.get("carrier_ids")

        try:
            carrier_ids = [int(x) for x in carrier_ids.split(",")]
        except Exception as e:
            errors.append({"carrier_ids": "Param: 'carrier_ids' not found, must be comma separated list of ints."})
            return Utility.json_error_response(code="900", message="Pickup Validate: invalid data.", errors=errors)

        pickup_restrictions = CarrierPickupRestriction.objects.select_related("carrier").filter(
            carrier__code__in=carrier_ids
        )

        if not pickup_restrictions:
            return Utility.json_response(data=[CarrierPickupRestriction.default_pickup_restrictions()])

        serializer = PickupRestrictionSerializer(pickup_restrictions, many=True)
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PickupValidateSerializer,
        operation_id='Validate Pickup Restriction',
        operation_description='Validate the carrier pickup request to ensure the date and pickup window are '
                              'valid for the carrier.',
        responses={
            "200": "Pickup is Valid",
            "400": "Bad Request",
            "500": "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Validate the carrier pickup request to ensure the date and pickup window are validate for the carrier.
            :param request: data
            :return: Message and boolean of success
        """

        json_data = request.data
        serializer = PickupValidateSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="901", message="Pickup Validate: Invalid values.", errors=serializer.errors
            )

        try:
            PickupValidate(pickup_request=serializer.validated_data).validate()
        except PickupException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data={"message": "Pickup is Valid", "success": True})
