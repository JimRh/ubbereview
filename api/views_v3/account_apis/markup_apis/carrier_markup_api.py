"""
    Title: Carrier Markup api views
    Description: This file will contain all functions for carrier serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import CarrierMarkup, CarrierMarkupHistory
from api.serializers_v3.private.account.carrier_markup_history_serializers import PrivateCarrierMarkupHistorySerializer
from api.serializers_v3.private.account.carrier_markup_serializers import PrivateCarrierMarkupSerializer, \
    PrivateUpdateCarrierMarkupSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class CarrierMarkupApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    # Customs
    _cache_lookup_key = "carrier_markups"

    def get_queryset(self):
        """
            Get initial carrier markups queryset and apply query params to the queryset.
            :return:
        """
        lookup_key = f'{self._cache_lookup_key}_{self.request.query_params["markup_id"]}'
        data = cache.get(lookup_key)

        if not data:
            data = CarrierMarkup.objects.select_related("markup", "carrier").filter(
                markup__id=self.request.query_params["markup_id"]
            )

            # Store metrics for 5 hours
            cache.set(lookup_key, data, TWENTY_FOUR_HOURS_CACHE_TTL)

        return data

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter(
            'markup_id', openapi.IN_QUERY, description="Markup Id", type=openapi.TYPE_INTEGER, required=True
        )],
        operation_id='Get Carrier Markups',
        operation_description='Get a list of carrier markup for a markup that contains the markup percentage.',
        responses={
            '200': openapi.Response('Get Carrier Markups', PrivateCarrierMarkupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier markups for the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'markup_id' not in self.request.query_params:
            errors.append({"carrier_markup": "Missing 'markup_id' parameter."})
            return Utility.json_error_response(
                code="3900", message="CarrierMarkup: Missing 'markup_id' parameter.", errors=errors
            )

        carrier_markups = self.get_queryset()
        carrier_markups = self.filter_queryset(queryset=carrier_markups)
        serializer = PrivateCarrierMarkupSerializer(carrier_markups, many=True)

        return Utility.json_response(data=serializer.data)


class CarrierMarkupDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put']

    # Customs
    _cache_lookup_key = "carrier_markups"
    _cache_lookup_key_individual = "carrier_markups_"
    _sub_account = None

    def get_object(self, markup_id=None):
        """
            Returns the object the view is displaying.
        """
        errors = []

        if not markup_id:
            markup_id = self.request.query_params["markup_id"]

        try:
            obj = CarrierMarkup.objects.select_related("markup", "carrier").get(
                markup__id=markup_id,
                pk=self.kwargs["pk"]
            )
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter(
            'markup_id', openapi.IN_QUERY, description="Markup Id", type=openapi.TYPE_INTEGER, required=True
        )],
        operation_id='Get Carrier Markup',
        operation_description='Get carrier markup for a markup that contains the markup percentage.',
        responses={
            '200': openapi.Response('Get Carrier Markup', PrivateCarrierMarkupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier markup information.
            :return: Json of carrier markup.
        """
        errors = []
        lookup_key = f'{self._cache_lookup_key_individual}_{self.kwargs["pk"]}'

        if 'markup_id' not in self.request.query_params:
            errors.append({"carrier_markup": "Missing 'markup_id' parameter."})
            return Utility.json_error_response(
                code="3901", message="CarrierMarkup: Missing 'markup_id' parameter.", errors=errors
            )

        cached_markup = cache.get(lookup_key)

        if not cached_markup:

            try:
                carrier_markup = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateCarrierMarkupSerializer(instance=carrier_markup, many=False)
            cached_markup = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_markup, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_markup)

    @swagger_auto_schema(
        request_body=PrivateCarrierMarkupSerializer,
        operation_id='Update Carrier Markup',
        operation_description='Update a carrier markup percentage.',
        responses={
            '200': openapi.Response('Update Carrier Markup', PrivateCarrierMarkupSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update carrier markup information
            :param request: request
            :return: Json of carrier markup.
        """
        # TODO CHANGE THIS TO BE A LIST OF CARRIERS instead of one to avoid 20 api calls?.
        errors = []
        json_data = request.data
        serializer = PrivateUpdateCarrierMarkupSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3903", message="CarrierMarkup: Invalid values.", errors=serializer.errors
            )

        try:
            carrier_markup = self.get_object(markup_id=serializer.validated_data["markup"]["id"])
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            carrier_markup = serializer.update(instance=carrier_markup, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3905", message="CarrierMarkup: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateCarrierMarkupSerializer(instance=carrier_markup, many=False)
        cache.delete(f"{self._cache_lookup_key}_{carrier_markup.markup.pk}")
        cache.delete(f'{self._cache_lookup_key_individual}_{self.kwargs["pk"]}')
        return Utility.json_response(data=serializer.data)


class CarrierMarkupHistoryApi(UbbeMixin, ListAPIView):
    http_method_names = ['get']

    # Customs
    _sub_account = None

    def get_queryset(self):
        """
            Get initial carrier markup history queryset and apply query params to the queryset.
            :return:
        """
        return CarrierMarkupHistory.objects.filter(
            carrier_markup__id=self.kwargs["pk"]
        )

    @swagger_auto_schema(
        operation_id='Get Carrier Markup Histories',
        operation_description='Get a carrier markup histories for a carrier markup which contains all changes that '
                              'occurred and who changed made the change.',
        responses={
            '200': openapi.Response('Get Markup Histories', PrivateCarrierMarkupHistorySerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier markup history for the system based on the allowed parameters and search params.
            :return:
        """

        histories = self.get_queryset()
        serializer = PrivateCarrierMarkupHistorySerializer(histories, many=True)

        return Utility.json_response(data=serializer.data)
