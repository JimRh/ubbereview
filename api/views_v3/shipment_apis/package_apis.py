"""
    Title: Packages Api Views V3
    Description: This file will contain all functions for Leg Api views
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.timezone import utc
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Package
from api.serializers_v3.common.package_serializer import PackageSerializer
from api.serializers_v3.private.shipments.package_serializers import CreatePackageSerializer
from api.utilities.utilities import Utility


class PackageApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'package_id', 'package_account_id', 'shipment__shipment_id', 'package_type', 'description', 'un_number',
        'dg_proper_name', 'container_number'
    ]

    # Customs
    _thirty_days = 30

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        if 'end_date' in self.request.query_params:
            end_date = datetime.strptime(self.request.query_params["end_date"], "%Y-%m-%d").replace(tzinfo=utc)
        else:
            end_date = datetime.now().replace(tzinfo=utc)

        if 'start_date' in self.request.query_params:
            start_date = datetime.strptime(self.request.query_params["start_date"], "%Y-%m-%d").replace(tzinfo=utc)
        else:
            start_date = end_date - timedelta(days=self._thirty_days)

        packages = Package.objects.select_related(
            "shipment__subaccount",
        ).filter(shipment__creation_date__range=[start_date, end_date])

        if self._sub_account.is_bbe and 'account' in self.request.query_params:
            packages = packages.filter(shipment__subaccount__subaccount_number=self.request.query_params["account"])
        else:
            packages = packages.filter(shipment__subaccount=self._sub_account)

        if 'is_dangerous_good' in self.request.query_params:
            pass

        if 'is_pharma' in self.request.query_params:
            packages = packages.filter(is_pharma=self.request.query_params["is_pharma"])

        if 'is_time_sensitive' in self.request.query_params:
            packages = packages.filter(is_time_sensitive=self.request.query_params["is_time_sensitive"])

        if 'is_cos' in self.request.query_params:
            packages = packages.filter(is_cos=self.request.query_params["is_cos"])

        return packages

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        return PackageSerializer

    @swagger_auto_schema(
        operation_id='Get Packages',
        operation_description='Get a list of packages made in the system.',
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_dangerous_good', openapi.IN_QUERY, description="Only DG", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_pharma', openapi.IN_QUERY, description="Only Pharma", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_time_sensitive', openapi.IN_QUERY, description="Only Time Sensitive", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_cos', openapi.IN_QUERY, description="Only COS", type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            '200': openapi.Response('Get Shipments', PackageSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipments based on the allowed parameters and determine..
            :return:
        """

        packages = self.get_queryset()
        packages = self.filter_queryset(queryset=packages)
        serializer = self.get_serializer_class()
        serializer = serializer(packages, many=True)

        return Utility.json_response(data=serializer.data)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        """
            Create shipment leg to be added to shipment.
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        shipment_id = (json_data[0]['shipment_id'])

        packages = []
        i = 1

        try:
            shipments_count = Package.objects.filter(package_id__startswith=shipment_id).count()
        except:
            raise Exception

        for package in json_data:
            serializer = CreatePackageSerializer(data=package, many=False)

            if not serializer.is_valid():
                return Utility.json_error_response(
                    code="2800", message="Package: Invalid values.", errors=serializer.errors
                )
            serializer.validated_data["package_id"] = f'{package["shipment_id"]}-{shipments_count + i}'
            try:
                instance = serializer.create(validated_data=serializer.validated_data)
            except ValidationError as e:
                errors.extend([{x: y} for x, y in e.message_dict.items()])
                return Utility.json_error_response(code="2801", message="Package: Failed to save.", errors=errors)
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            packages.append(instance)
            i += 1

        response_serializer = self.get_serializer_class()
        response_serializer = response_serializer(packages, many=True)

        return Utility.json_response(data=response_serializer.data)


class PackageDetailApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """
        packages = Package.objects.select_related(
            "shipment__subaccount",
        ).filter(shipment__shipment_id=self.kwargs["shipment_id"])

        if not self._sub_account.is_bbe:
            packages = packages.filter(shipment__subaccount=self._sub_account)

        if 'package_id' in self.request.query_params:
            packages = packages.filter(package_id=self.request.query_params["package_id"])

        return packages

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        return PackageSerializer

    @swagger_auto_schema(
        operation_id='Get Shipment Packages',
        operation_description='Get a list of packages made in the system.',
        manual_parameters=[
            openapi.Parameter(
                'start_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY, description="Date: YYYY-mm-dd", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_dangerous_good', openapi.IN_QUERY, description="Only DG", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_pharma', openapi.IN_QUERY, description="Only Pharma", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_time_sensitive', openapi.IN_QUERY, description="Only Time Sensitive", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'is_cos', openapi.IN_QUERY, description="Only COS", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'package_id', openapi.IN_QUERY, description="Get individual package", type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            '200': openapi.Response('Get Shipment Packages', PackageSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipment packages for a shipment or individual package based on the allowed parameters and determine.
            :return:
        """

        packages = self.get_queryset()
        serializer = self.get_serializer_class()
        serializer = serializer(packages, many=True)

        return Utility.json_response(data=serializer.data)
