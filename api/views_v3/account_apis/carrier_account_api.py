"""
    Title: Carrier Account api views
    Description: This file will contain all functions for carrier accounts serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import CarrierAccount
from api.serializers_v3.private.account.carrier_account_serializers import PrivateCarrierAccountSerializer, \
    PrivateCreateCarrierAccountSerializer, PrivateUpdateCarrierAccountSerializer

# TODO - Should this be cached or not.
from api.utilities.utilities import Utility


class CarrierAccountApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
            Get initial carrier accounts queryset and apply query params to the queryset.
            :return:
        """

        accounts = CarrierAccount.objects.select_related(
            "carrier",
            "subaccount__contact",
            "carrier",
            "api_key",
            "contract_number",
            "account_number",
            "username",
            "password"
        ).all().order_by("carrier__name")

        if 'account' in self.request.query_params:
            accounts = accounts.filter(subaccount__subaccount_number=self.request.query_params["account"])

        if 'carrier_code' in self.request.query_params:
            accounts = accounts.filter(carrier__code=self.request.query_params["carrier_code"])

        return accounts

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'account',
                openapi.IN_QUERY,
                description="Sub Account Number",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            ),
            openapi.Parameter(
                'carrier_code', openapi.IN_QUERY, description="Carrier Code", type=openapi.TYPE_INTEGER
            )
        ],
        operation_id='Get Carrier Accounts',
        operation_description='Get a list of carrier accounts for a sub account that contains api keys, passwords, '
                              'usernames, and account numbers. This information in stored has encrypted values.',
        responses={
            '200': openapi.Response('Get Carrier Accounts', PrivateCarrierAccountSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier accounts for the system based on the allowed parameters and search params.
            :return:
        """

        markups = self.get_queryset()
        serializer = PrivateCarrierAccountSerializer(markups, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateCreateCarrierAccountSerializer,
        operation_id='Create Carrier Account',
        operation_description='Create an carrier account for a sub account that contains api keys, passwords, '
                              'usernames, and account numbers. This information in stored has encrypted values.',
        responses={
            '200': openapi.Response('Create Carrier Account', PrivateCarrierAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new bill of lading.
            :param request: request
            :return: json of bill of lading.
        """
        errors = []
        json_data = request.data
        serializer = PrivateCreateCarrierAccountSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3600", message="CarrierAccount: Invalid values.", errors=serializer.errors
            )

        try:
            service = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3601", message="CarrierAccount: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateCarrierAccountSerializer(instance=service, many=False)

        return Utility.json_response(data=serializer.data)


class CarrierAccountDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = CarrierAccount.objects.select_related(
                "carrier",
                "subaccount__contact",
                "carrier",
                "api_key",
                "contract_number",
                "account_number",
                "username",
                "password"
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"api": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4103", message="Api: Object Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Carrier Account',
        operation_description='Get a carrier account for a sub account that contains api keys, passwords, '
                              'usernames, and account numbers. This information in stored has encrypted values.',
        responses={
            '200': openapi.Response('Get Carrier Account', PrivateCarrierAccountSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get carrier account information.
            :return: Json of carrier account.
        """

        try:
            carrier_account = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = PrivateCarrierAccountSerializer(instance=carrier_account, many=False)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateUpdateCarrierAccountSerializer,
        operation_id='Update Carrier Account',
        operation_description='Update an carrier account that includes api keys, passwords, usernames, and account '
                              'numbers. This information in stored has encrypted values.',
        responses={
            '200': openapi.Response('Update Carrier Account', PrivateUpdateCarrierAccountSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update carrier account information
            :param request: request
            :return: Json of carrier account.
        """
        errors = []
        json_data = request.data
        serializer = PrivateUpdateCarrierAccountSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="3604", message="CarrierAccount: Invalid values.", errors=serializer.errors
            )

        try:
            carrier_account = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            carrier_account = serializer.update(instance=carrier_account, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="3606", message="CarrierAccount: Failed to update.", errors=errors)

        serializer = PrivateCarrierAccountSerializer(instance=carrier_account, many=False)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Carrier Account',
        operation_description='Delete an carrier account for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete carrier account from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            carrier_account = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        carrier_account.delete()

        return Utility.json_response(data={"carrier_account": self.kwargs["pk"], "message": "Successfully Deleted"})
