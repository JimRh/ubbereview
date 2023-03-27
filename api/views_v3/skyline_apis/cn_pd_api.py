"""
    Title: 5T Northern PD Address Api
    Description: This file will contain all functions for 5T northern pd address apis.
    Created: December 02, 2021
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
from api.models import NorthernPDAddress
from api.serializers_v3.private.cn.northern_pd_address_serializers import PrivateNorthernPDAddressSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CNNorthernPDAddressApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['pickup_id', 'delivery_id', 'city_name']

    # Customs
    _cache_lookup_key = "cn_pickup_delivery"

    def get_queryset(self):
        """
            Get initial 5t transit times queryset and apply query params to the queryset.
            :return:
        """

        pds = cache.get(self._cache_lookup_key)

        if not pds:
            pds = NorthernPDAddress.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, pds, TWENTY_FOUR_HOURS_CACHE_TTL)

        return pds

    @swagger_auto_schema(
        operation_id='Get CN Pickup Delivery Costs',
        operation_description='Get a list of canadian north pickup and delivery costs per location.',
        responses={
            '200': openapi.Response('Get CN Pickup Delivery Costs', PrivateNorthernPDAddressSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get transit times for a carrier based on the allowed parameters and search params.
            :return:
        """

        pds = self.get_queryset()
        pds = self.filter_queryset(queryset=pds)
        serializer = PrivateNorthernPDAddressSerializer(pds, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateNorthernPDAddressSerializer,
        operation_id='Create CN Pickup Delivery Cost',
        operation_description='Create a canadian north pickup and delivery costs for a location.',
        responses={
            '200': openapi.Response('Create CN Pickup Delivery Cost', PrivateNorthernPDAddressSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new 5t northern pd address.
            :param request: request
            :return: 5t northern pd address json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateNorthernPDAddressSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6000", message="CN PD: Invalid values.", errors=serializer.errors
            )

        try:
            pd = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6001", message="CN PD: Failed to save.", errors=errors)
        except ViewException as e:
            errors.append({"cn_pd_address": e.message})
            return Utility.json_error_response(code="6002", message="CN PD: Failed to save.", errors=errors)

        serializer.instance = pd
        cache.delete(self._cache_lookup_key)

        return Utility.json_response(data=serializer.data)


class CNNorthernPDAddressDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "cn_pickup_delivery"
    _cache_lookup_key_individual = "cn_pickup_delivery_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = NorthernPDAddress.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"cn_pd_address": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="6003", message="CN PD: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get CN Pickup Delivery Cost',
        operation_description='Get a canadian north pickup and delivery cost for a location.',
        responses={
            '200': openapi.Response('Get CN Pickup Delivery Cost', PrivateNorthernPDAddressSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get 5t northern pd address information.
            :return: Json of 5t northern pd address
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_pd = cache.get(lookup_key)

        if not cached_pd:

            try:
                pd = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateNorthernPDAddressSerializer(instance=pd, many=False)
            cached_pd = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_pd, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_pd)

    @swagger_auto_schema(
        request_body=PrivateNorthernPDAddressSerializer,
        operation_id='Update CN Pickup Delivery Cost',
        operation_description='Update a canadian north pickup and delivery cost for a location.',
        responses={
            '200': openapi.Response('Update CN Pickup Delivery Cost', PrivateNorthernPDAddressSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update 5t northern pd address information
            :param request: request
            :return: Json of 5t northern pd address.
        """
        errors = []
        json_data = request.data
        serializer = PrivateNorthernPDAddressSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6004", message="CN PD: Invalid values.", errors=serializer.errors
            )

        try:
            pd = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            pd = serializer.update(instance=pd, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6006", message="CN PD: Failed to update.", errors=errors)
        except ViewException as e:
            errors.append({"cn_pd_address": e.message})
            return Utility.json_error_response(code="6007", message="CN PD: Failed to update.", errors=errors)

        serializer.instance = pd
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete CN Pickup Delivery Cost',
        operation_description='Delete an cn pickup delivery lane for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete 5t northern pd address from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            pd = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        pd.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"cn_pd_address": self.kwargs["pk"], "message": "Successfully Deleted"})
