"""
    Title:Business Central Customers Api views
    Description: This file will contain all functions for Business Central Customers Api.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.apis.business_central.business_central import BusinessCentral
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.utilities.utilities import Utility
from brain.settings import ONE_HOUR_CACHE_TTL


class BCCustomersApi(UbbeMixin, APIView):
    """
        ubbe Business Central Customers Api.
    """
    # Customs
    _cache_lookup_key = "business_central_customers"

    @swagger_auto_schema(
        operation_id='Get BC Customers',
        operation_description='Get a list of business central customers.',
        responses={
            '200': "List of customers.",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request):
        """
            Get all business central customers for ubbe.
            :param request:
            :return:
        """
        bc_customers = cache.get(self._cache_lookup_key)

        if not bc_customers:

            try:
                bc_customers = BusinessCentral().get_customers()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            # Store metrics for 1 hour
            cache.set(self._cache_lookup_key, bc_customers, ONE_HOUR_CACHE_TTL)

        return Utility.json_response(data=bc_customers)


class BCItemsApi(UbbeMixin, APIView):
    """
        ubbe Business Central Items Api.
    """

    # Customs
    _cache_lookup_key = "business_central_items"

    @swagger_auto_schema(
        operation_id='Get BC items',
        operation_description='Get a list of business central items.',
        responses={
            '200': "List of items.",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request):
        """
            Get all business central items for ubbe.
            :param request:
            :return:
        """

        bc_items = cache.get(self._cache_lookup_key)

        if not bc_items:

            try:
                bc_items = BusinessCentral().get_items()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            # Store metrics for 1 hour
            cache.set(self._cache_lookup_key, bc_items, ONE_HOUR_CACHE_TTL)

        return Utility.json_response(data=bc_items)


class BCVendorsApi(UbbeMixin, APIView):
    """
        ubbe Business Central Vendors Api.
    """

    # Customs
    _cache_lookup_key = "business_central_vendors"

    @swagger_auto_schema(
        operation_id='Get BC Vendors',
        operation_description='Get a list of business central vendors.',
        responses={
            '200': "List of vendors.",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request):
        """
            Get all business central vendors for ubbe.
            :param request:
            :return:
        """

        bc_vendors = cache.get(self._cache_lookup_key)

        if not bc_vendors:

            try:
                bc_vendors = BusinessCentral().get_vendors()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            # Store metrics for 1 hour
            cache.set(self._cache_lookup_key, bc_vendors, ONE_HOUR_CACHE_TTL)

        return Utility.json_response(data=bc_vendors)


class BCJobListApi(UbbeMixin, APIView):
    """
        ubbe Business Central Job List Api.
    """

    @staticmethod
    @swagger_auto_schema(
        operation_id='Get BC Jobs',
        operation_description='Get a list of business central active jobs.',
        responses={
            '200': "List of jobs.",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(request):
        """
            Get business central Job List for ubbe.
            :param request:
            :return:
        """

        username = request.GET.get("username", "")
        is_all = request.GET.get("is_all", False) == "true"

        try:
            bc_job_list = BusinessCentral().get_job_list(username=username, is_all=is_all)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=bc_job_list)
