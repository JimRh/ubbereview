"""
    Title: Rate Sheet api views
    Description: This file will contain all functions for rate sheet api functions.
    Created: November 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import RateSheet
from api.serializers_v3.private.rate_sheets.rs_serializers import RateSheetSerializer, CreateRateSheetSerializer, \
    DeleteRateSheetSerializer
from api.utilities.utilities import Utility

# TODO - Add pagination to get to handle 2000 plus rs lanes


class RateSheetApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post', 'delete']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'rs_type', 'carrier__name', 'carrier__code', 'origin_city', 'destination_city', 'service_code', 'service_name'
    ]

    def get_queryset(self):
        """
            Get initial rate sheets queryset and apply query params to the queryset.
            :return:
        """

        sheets = RateSheet.objects.select_related(
            "sub_account",
            "carrier",
            "origin_province__country",
            "destination_province__country"
        ).filter(carrier__code=self.request.query_params["carrier_code"])

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            sheets = sheets.filter(sub_account__subaccount_number=self.request.query_params["account"])
        else:
            sheets = sheets.filter(sub_account=self._sub_account)

        if 'rs_type' in self.request.query_params:
            sheets = sheets.filter(rs_type=self.request.query_params["rs_type"])

        if 'service_code' in self.request.query_params:
            sheets = sheets.filter(service_code=self.request.query_params["service_code"])

        return sheets

    @swagger_auto_schema(
        operation_id='Get Rate Sheets',
        operation_description='Get an rate sheet for a carrier which includes the origin, destination, transit time, '
                              'service days, and other information.',
        manual_parameters=[
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER, required=True
            ),
            openapi.Parameter(
                'rs_type', openapi.IN_QUERY, description="RS Type: Calculation Type", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'service_code', openapi.IN_QUERY, description="Service Code", type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            '200': openapi.Response('Get Rate Sheets', RateSheetSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get rate sheets for a carrier in the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'carrier_code' not in self.request.query_params:
            errors.append({"rate_sheet": "Missing 'carrier_code' parameter."})
            return Utility.json_error_response(
                code="6200", message="RateSheet: Missing 'carrier_code' parameter.", errors=errors
            )

        sheets = self.get_queryset()
        sheets = self.filter_queryset(queryset=sheets)
        serializer = RateSheetSerializer(sheets, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=CreateRateSheetSerializer,
        operation_id='Create Rate Sheet',
        operation_description='Create a rate sheet lane for a carrier.',
        responses={
            '200': openapi.Response('Create Rate Sheet', CreateRateSheetSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new rate sheet.
            :param request: request
            :return: Json of rate sheet.
        """
        errors = []
        json_data = request.data
        serializer = CreateRateSheetSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6201", message="RateSheet: Invalid values.", errors=serializer.errors
            )

        try:
            rate_sheet = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6202", message="RateSheet: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = rate_sheet

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Rate Sheet',
        operation_description='Delete all rate sheets for a carrier, or if specified delete certain service levels.',
        request_body=DeleteRateSheetSerializer,
        responses={
            '200': "All Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete all rate sheets for a carrier from the system.
            :param request: request
            :return: Success rate sheet.
        """

        json_data = request.data
        serializer = DeleteRateSheetSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6204", message="RateSheet: Invalid values.", errors=serializer.errors
            )

        sheets = RateSheet.objects.filter(
            sub_account__subaccount_number=serializer.validated_data["sub_account"]["subaccount_number"],
            carrier__code=serializer.validated_data["carrier"]["code"],
        )

        if 'service_code' in serializer.validated_data and serializer.validated_data['service_code']:
            sheets = sheets.filter(service_code=serializer.validated_data['service_code'])

        sheets.delete()

        return Utility.json_response(data={"rate_sheet": "All", "message": "All Successfully Deleted"})


class RateSheetDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = RateSheet.objects.select_related(
                "sub_account",
                "carrier",
                "origin_province__country",
                "destination_province__country"
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"rate_sheet": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="6205", message="RateSheet: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Rate Sheet',
        operation_description='Get an rate sheet for a carrier which includes the origin, destination, transit time, '
                              'service days, and other information.',
        responses={
            '200': openapi.Response('Get Rate Sheet', RateSheetSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get rate sheet information.
            :return: Json of rate sheet.
        """

        try:
            rate_sheet = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = RateSheetSerializer(instance=rate_sheet, many=False)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=RateSheetSerializer,
        operation_id='Update Rate Sheet',
        operation_description='Update an airbase address information or the airport code.',
        responses={
            '200': openapi.Response('Update Rate Sheet', RateSheetSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update rate sheet information
            :param request: request
            :return: Json of rate sheet.
        """
        errors = []
        json_data = request.data
        serializer = RateSheetSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6206", message="RateSheet: Invalid values.", errors=serializer.errors
            )

        try:
            rate_sheet = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            rate_sheet = serializer.update(instance=rate_sheet, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6208", message="RateSheet: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = rate_sheet
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Rate Sheet',
        operation_description='Delete an rate sheet for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete rate sheet from the system.
            :param request: request
            :return: Success rate sheet.
        """

        try:
            rate_sheet = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        rate_sheet.delete()

        return Utility.json_response(data={"rate_sheet": self.kwargs["pk"], "message": "Successfully Deleted"})
