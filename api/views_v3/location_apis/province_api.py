"""
    Title: Province  Serializers
    Description: This file will contain all functions for province serializers.
    Created: November 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Province, Country
from api.serializers_v3.common.province_serializer import ProvinceSerializer, ProvinceDetailSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class GetProvinces(UbbeMixin, APIView):
    """
        Get a List of all provinces for a country.
    """
    province_response = openapi.Response('Provinces', ProvinceSerializer(many=True))

    # Customs
    _cache_lookup_key = "provinces_"

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'country', openapi.IN_QUERY, description="Country Code", type=openapi.TYPE_STRING, required=True
            )
        ],
        operation_id='Get Provinces',
        operation_description='Get all provinces for a country including their name and code.',
        responses={
            '200': openapi.Response('Get Provinces', ProvinceSerializer(many=True)),
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get all provinces for a country.
            :param request: request.
            :return: Json list of provinces.
        """
        errors = []
        country = self.request.GET.get("country")

        if not country:
            errors.append({"province": "Missing 'country' parameter."})
            return Utility.json_error_response(
                code="1500", message="Province: Missing 'country' parameter.", errors=errors
            )

        if not Country.objects.filter(code=country).exists():
            errors.append({"province": "'country' does not exist."})
            return Utility.json_error_response(
                code="1501", message="Province: 'country' does not exist.", errors=errors
            )

        lookup_key = f"provinces_{country.lower()}"
        data = cache.get(lookup_key)

        if not data:
            provinces = Province.objects.filter(country__code=country).order_by("name")
            serializer = ProvinceSerializer(provinces, many=True)
            data = serializer.data
            cache.set(lookup_key, data, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'country', openapi.IN_QUERY, description="Country Code", type=openapi.TYPE_STRING, required=True
            )
        ],
        request_body=ProvinceSerializer,
        operation_id='Create Province',
        operation_description='Create a province for a country including their name and code.',
        responses={
            '200': openapi.Response('Create Province', ProvinceSerializer(many=True)),
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new province.
            :param request: request
            :return: Json of province.
        """
        errors = []
        country = self.request.GET.get("country")

        if not country:
            errors.append({"province": "Missing 'country' parameter."})
            return Utility.json_error_response(
                code="1500", message="Province: Missing 'country' parameter.", errors=errors
            )

        json_data = request.data
        serializer = ProvinceSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1504", message="Province: Invalid values.", errors=serializer.errors
            )

        serializer.validated_data["country"] = country

        try:
            province = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1502", message="Province: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f"{self._cache_lookup_key}{country.lower()}")
        serializer.instance = province

        return Utility.json_response(data=serializer.data)


class ProvinceDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "provinces_"
    _cache_lookup_key_individual = "provinces_individual_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Province.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"province": f'PK: {self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1505", message="Province: not found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Province',
        operation_description='Get a province for a country including their name and code.',
        responses={
            '200': openapi.Response('Get Province', ProvinceSerializer(many=True)),
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get province information.
            :return:
        """
        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_province = cache.get(lookup_key)

        if not cached_province:

            try:
                province = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = ProvinceDetailSerializer(province, many=False)
            cached_province = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_province, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_province)

    @swagger_auto_schema(
        request_body=ProvinceDetailSerializer,
        operation_id='Update Province',
        operation_description='Update an province for a country including their name and code.',
        responses={
            '200': openapi.Response('Update Province', ProvinceDetailSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update province information
            :param request: request
            :return: Json of province.
        """
        errors = []
        json_data = request.data
        serializer = ProvinceDetailSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1507", message="Province: Invalid values.", errors=serializer.errors
            )

        try:
            province = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            province = serializer.update(instance=province, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1506", message="Province: failed to update.", errors=errors)

        cache.delete(f"{self._cache_lookup_key}{province.country.code.lower()}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        serializer.instance = province
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Province',
        operation_description='Delete an province for a country.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete province from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            province = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        cache.delete(f"{self._cache_lookup_key}{province.country.code.lower()}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')
        province.delete()

        return Utility.json_response(data={"province": self.kwargs["pk"], "message": "Successfully Deleted"})
