"""
    Title: Carrier Api
    Description: This file will contain all functions for carrier apis.
    Created: November 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Carrier
from api.serializers_v3.private.carriers.carrier_serializers import PrivateCarrierSerializer, PrivateCreateCarrierSerializer
from api.serializers_v3.public.carrier_serializers import PublicCarrierSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CarrierApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name', 'bc_vendor_code', 'mode', 'type']

    # Customs
    _cache_lookup_key = "carriers"

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """
        carriers = cache.get(self._cache_lookup_key)

        if not carriers:
            carriers = Carrier.objects.all()

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, carriers, TWENTY_FOUR_HOURS_CACHE_TTL)

        if 'is_kilogram' in self.request.query_params:
            carriers = carriers.filter(is_kilogram=self.request.query_params["is_kilogram"])

        if 'is_dangerous_good' in self.request.query_params:
            carriers = carriers.filter(is_dangerous_good=self.request.query_params["is_dangerous_good"])

        if 'is_pharma' in self.request.query_params:
            carriers = carriers.filter(is_dangerous_good=self.request.query_params["is_pharma"])

        carrier_types = ["AP", "RS", "MC", "NA"]

        if "is_remove_manual" in self.request.query_params:
            carrier_types.remove('MC')

        if "is_remove_disabled" in self.request.query_params:
            carrier_types.remove('NA')

        carriers = carriers.filter(type__in=carrier_types)

        return carriers

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PrivateCarrierSerializer
        else:
            return PublicCarrierSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'is_kilogram',
                openapi.IN_QUERY,
                description="Metric carriers only, False fo imperial.",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_dangerous_good', openapi.IN_QUERY, description="DG carriers only.", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_pharma', openapi.IN_QUERY, description="Pharma carriers only.", type=openapi.TYPE_BOOLEAN
            )
        ],
        operation_id='Get Carriers',
        operation_description='Get a list of carriers that contains what type and mode of carrier they are, if they '
                              'are able to perform dangerous goods or pharma shipments.',
        responses={
            '200': openapi.Response('Get Carriers', PublicCarrierSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carriers based on the allowed parameters and search paramms.
            :return:
        """

        carriers = self.get_queryset()
        carriers = self.filter_queryset(queryset=carriers)
        serializer = self.get_serializer_class()
        serializer = serializer(carriers, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateCarrierSerializer,
        operation_id='Create Carrier',
        operation_description='Create an carrier that contains what type and mode of carrier they are, if they '
                              'are able to perform dangerous goods or pharma shipments.',
        responses={
            '200': openapi.Response('Create Carrier', PrivateCreateCarrierSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new Carrier.
            :param request: request
            :return: Carrier json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateCarrierSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1600", message="Carrier: Invalid values.", errors=serializer.errors
            )

        try:
            carrier = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1601", message="Carrier: Failed to save.", errors=errors)

        serializer.instance = carrier
        cache.delete(self._cache_lookup_key)
        cache.delete(f"carrier_list_mode_{carrier.mode}")

        return Utility.json_response(data=serializer.data)


class CarrierDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put']

    # Customs
    _cache_lookup_key = "carriers"
    _cache_lookup_key_individual = "carriers_"
    _sub_account = None

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Carrier.objects.get(code=self.kwargs["code"])
        except ObjectDoesNotExist:
            errors.append({"carrier": f'{self.kwargs["code"]} not found or you do not have permission.'})
            raise ViewException(code="1602", message="Carrier: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Carrier',
        operation_description='Get a carrier that contains what type and mode of carrier they are, if they are able '
                              'to perform dangerous goods or pharma shipments.',
        responses={
            '200': openapi.Response('Get Carrier', PrivateCarrierSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier information.
            :return: Json of carrier.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["code"]}'
        cached_carrier = cache.get(lookup_key)

        if not cached_carrier:

            try:
                carrier = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateCarrierSerializer(instance=carrier, many=False)
            cached_carrier = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_carrier, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_carrier)

    @swagger_auto_schema(
        request_body=PrivateCarrierSerializer,
        operation_id='Update Carrier',
        operation_description='Update an carrier information including what type and mode of carrier they are, if '
                              'they are able to perform dangerous goods or pharma shipments.',
        responses={
            '200': openapi.Response('Update Carrier', PrivateCarrierSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update carrier information
            :param request: request
            :return: Json of carrier.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCarrierSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1603", message="Carrier: Invalid values.", errors=serializer.errors
            )

        try:
            carrier = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        previous_mode = copy.deepcopy(carrier.mode)

        try:
            carrier = serializer.update(instance=carrier, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1604", message="Carrier: Failed to update.", errors=errors)

        serializer.instance = carrier
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["code"]}')
        cache.delete(f"carrier_list_mode_{carrier.mode}")
        cache.delete(f"carrier_list_mode_{previous_mode}")

        return Utility.json_response(data=serializer.data)
