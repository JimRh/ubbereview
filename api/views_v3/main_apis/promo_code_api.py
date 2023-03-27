"""
    Title: Promo Code api views
    Description: This file will contain all functions for Promo Code api functions.
    Created: June 2, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from api.apis.promo_code.promo_code import PromoCodeUtility
from api.apis.reports.bulk_promo_codes_report import BulkPromoCodesReport
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import PromoCode
from api.serializers_v3.common.promo_code_serializer import PromoCodeSerializer, PromoCodeBulkSerializer, \
    PromoCodeValidateSerializer, PromoCodeValidateResponseSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL, FIVE_HOURS_CACHE_TTL


class PromoCodeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'start_date', 'end_date', 'quantity', 'flat_amount', 'min_shipment_cost', 'max_discount', 'percentage', 'is_active', 'is_bulk', 'amount']

    # Customs
    _cache_lookup_key = "promo_code"

    def get_queryset(self):
        """
            Get initial promo code queryset and apply query params to the queryset.
            :return:
        """

        promos = cache.get(f"{self._cache_lookup_key}")

        if not promos:
            promos = PromoCode.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, promos, FIVE_HOURS_CACHE_TTL)

        return promos

    @swagger_auto_schema(
        operation_id='Get Promo Code',
        operation_description='Get a list of promo codes available in the system.',

        responses={
            '200': openapi.Response('Get Promo Code', PromoCodeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get promo codes for the system based on the allowed parameters and search params.
            :return:
        """

        promos = self.get_queryset()
        promos = self.filter_queryset(queryset=promos)
        serializer = PromoCodeSerializer(promos, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PromoCodeSerializer,
        operation_id='Create Promo Code',
        operation_description='Create a promo code for the system.',
        responses={
            '200': openapi.Response('Create Promo Code', PromoCodeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new promo code.
            :param request: request
            :return: Json of promo code.
        """
        errors = []
        json_data = request.data
        serializer = PromoCodeSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1200", message="Promo Code: Invalid values.", errors=serializer.errors
            )
        try:
            promo = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1201", message="Promo Code: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = promo
        cache.delete(f"{self._cache_lookup_key}")

        return Utility.json_response(data=serializer.data)


class PromoCodeDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "promo_code"
    _cache_lookup_key_individual = "promo_code_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = PromoCode.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"promo_code": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="1103", message="Promo Code: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Promo Code',
        operation_description='Get a promo code available in the system.',
        responses={
            '200': openapi.Response('Get Promo Code', PromoCodeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get promo code information.
            :return: Json of promo code.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_promo = cache.get(lookup_key)

        if not cached_promo:

            try:
                promo = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PromoCodeSerializer(instance=promo, many=False)
            cached_promo = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_promo, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_promo)

    @swagger_auto_schema(
        request_body=PromoCodeSerializer,
        operation_id='Update Promo Code',
        operation_description='Update a promo code in the system.',
        responses={
            '200': openapi.Response('Update Promo Code', PromoCodeSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Promo Code information
            :param request: request
            :return: Json of web promo.
        """
        errors = []
        json_data = request.data
        serializer = PromoCodeSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1204", message="Promo Code: Invalid values.", errors=serializer.errors
            )

        try:
            promo = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            promo = serializer.update(instance=promo, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1206", message="Promo Code: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = promo
        cache.delete(f"{self._cache_lookup_key}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Promo Code',
        operation_description='Deactivate a promo code.',
        responses={
            '200': "Successfully Deactivated",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Deactivate a promo code.
            :param request: request
            :return: Success message.
        """

        try:
            promo = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        promo.is_active = False
        promo.save()
        cache.delete(f"{self._cache_lookup_key}")
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"Promo Code": self.kwargs["pk"], "message": "Successfully Deactivated"})


class PromoCodeBulkApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'start_date', 'end_date', 'quantity', 'flat_amount', 'min_shipment_cost', 'max_discount',
                     'percentage', 'is_active', 'is_bulk', 'amount']

    # Customs
    _cache_lookup_key = "promo_code"

    def post(self, request, *args, **kwargs):
        """
            Create a new promo code.
            :param request: request
            :return: Json of promo code.
        """
        errors = []
        json_data = request.data
        serializer = PromoCodeBulkSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1200", message="Promo Code: Invalid values.", errors=serializer.errors
            )
        bulk_list = []
        for i in range(0, int(serializer.validated_data['amount'])):
            try:
                promo = serializer.create(validated_data=serializer.validated_data)
            except ValidationError as e:
                errors.extend([{x: y} for x, y in e.message_dict.items()])
                return Utility.json_error_response(code="1201", message="Promo Code: failed to save.", errors=errors)
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)
            bulk_list.append([promo.code])

        cache.delete(f"{self._cache_lookup_key}")
        try:
            bulk_promo_data = BulkPromoCodesReport().get_bulk(file_name=f'bulk_promo_codes_.xlsx', bulk_list=bulk_list)
        except ViewException as e:
            errors.append({"bulk_promo_codes": e.message})
            return Utility.json_error_response(code="3202", message="BulkPromoCodes: failed to create.", errors=errors)

        return Utility.json_response(data=bulk_promo_data)


class PromoCodeValidateApi(UbbeMixin, APIView):
    http_method_names = ['post']

    @swagger_auto_schema(
        request_body=PromoCodeValidateSerializer,
        operation_id='Validate Promo Code',
        operation_description='Validate promo code and get the discount amount.',
        responses={
            "200": openapi.Response('Validate Promo Code', PromoCodeValidateResponseSerializer(many=False)),
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
        serializer = PromoCodeValidateSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="901", message="Promo Code: Invalid values.", errors=serializer.errors
            )

        try:
            ret = PromoCodeUtility().get_discount(data=serializer.validated_data)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=ret)
