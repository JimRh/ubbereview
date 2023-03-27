"""
    Title: Dangerous Goods Apis
    Description: This file will contain all functions for dangerous goods api.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGood
from api.serializers.old.dg_serializers import GetDGUNNumberInfoSerializerRequest, GetDGUNNumberInfoSerializerResponse
from api.serializers_v3.private.dangerous_goods.dg_seralizers import DGSerializer, CreateDGSerializer

# TODO - Make update work
from api.utilities.utilities import Utility


class DangerousGoodApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['un_number', 'short_proper_shipping_name', 'verbose_proper_shipping_name', 'state']

    def get_queryset(self):
        """
            Get initial dangerous goods queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGood.objects.select_related(
            "classification",
            "packing_group",
            "specialty_label",
            "excepted_quantity",
        ).prefetch_related(
            "subrisks",
            "air_quantity_cutoff",
            "air_special_provisions",
            "ground_special_provisions"
        ).all().order_by("un_number")

    @swagger_auto_schema(
        operation_id='Get Dangerous Goods',
        operation_description='Get a list of dangerous goods that are supported in the system.',
        responses={
            '200': openapi.Response('Get Dangerous Goods', DGSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous goods based on the allowed parameters and search params.
            :return:
        """

        dgs = self.get_queryset()
        dgs = self.filter_queryset(queryset=dgs)
        serializer = DGSerializer(dgs, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Create Dangerous Good',
        operation_description='Create a dangerous good to add support for it.',
        responses={
            '200': openapi.Response('Create Dangerous Good', DGSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new dangerous good.
            :param request: request
            :return: json of dangerous good.
        """
        errors = []
        json_data = request.data
        serializer = CreateDGSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="4700", message="Dangerous Good: Invalid values.", errors=serializer.errors
            )

        try:
            dg = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="4701", message="Dangerous Good: Failed to save.", errors=errors)
        except ViewException as e:
            errors.append({"dangerous_goods": e.message})
            return Utility.json_error_response(code="4702", message="Dangerous Good: Failed to save.", errors=errors)

        serializer = DGSerializer(instance=dg, many=False)
        return Utility.json_response(data=serializer.data)


class DangerousGoodDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'delete']

    # Customs
    _sub_account = None

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = DangerousGood.objects.select_related(
                "classification",
                "packing_group",
                "specialty_label",
                "excepted_quantity",
            ).prefetch_related(
                "subrisks",
                "air_quantity_cutoff",
                "air_special_provisions",
                "ground_special_provisions"
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"dangerous_goods": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="4703", message="Dangerous Good: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Dangerous Good',
        operation_description='Get a dangerous good that is supported in the system.',
        responses={
            '200': openapi.Response('Get Dangerous Good', DGSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good information.
            :return: Json of dangerous good.
        """

        try:
            dg = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = DGSerializer(instance=dg, many=False)

        return Utility.json_response(data=serializer.data)

    # def put(self, request, *args, **kwargs):
    #     """
    #         Update dangerous good information
    #         :param request: request
    #         :return: Json of dangerous good.
    #     """
    #     errors = []
    #     json_data = request.data
    #     serializer = CreateDGSerializer(data=json_data, many=False, partial=True)
    #
    #     if not serializer.is_valid():
    #         return Utility.json_error_response(
    #             code="4704", message="Dangerous Good: Invalid values.", errors=serializer.errors
    #         )
    #
    #     try:
    #         dg = self.get_object()
    #     except ViewException as e:
    #         return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)
    #
    #     try:
    #         dg = serializer.update(instance=dg, validated_data=serializer.validated_data)
    #     except ValidationError as e:
    #         errors.extend([{x: y} for x, y in e.message_dict.items()])
    #         return Utility.json_error_response(code="4706", message="Dangerous Good Failed to update.", errors=errors)
    #
    #     serializer.instance = dg
    #     return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Dangerous Good',
        operation_description='Delete a dangerous good from the system',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete dangerous good from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            dg = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        dg.delete()

        return Utility.json_response(data={"dangerous_goods": self.kwargs["pk"], "message": "Successfully Deleted"})


class DGUNumberInfo(UbbeMixin, APIView):

    # Todo - Temporary api

    @staticmethod
    @swagger_auto_schema(
        query_serializer=GetDGUNNumberInfoSerializerRequest,
        responses={'200': openapi.Response('Post Account', GetDGUNNumberInfoSerializerResponse)},
        operation_id='Get DG UN number Info',
        operation_description='This gets the Dangerous good information from a given un number.',
    )
    def post(request):
        request_json = request.data

        try:
            un_number = request_json["un_number"]
        except KeyError as e:
            errors = [{"un_number": f"'un_number'is a required field"}]
            return Utility.json_error_response(
                code="4708", message="Dangerous Good: Missing 'un_number' field", errors=errors
            )

        if not isinstance(un_number, int):
            errors = [{"un_number": f"'un_number' must be a Integer"}]
            return Utility.json_error_response(
                code="4709", message="Dangerous Good: Invalid value.", errors=errors
            )

        data = DangerousGood.get_data(unnumber=un_number)

        if not data:
            errors = [{"un_number": f"Un Number: {un_number} not supported."}]
            return Utility.json_error_response(code="4710", message="Dangerous Good: Not Supported.", errors=errors)

        return Utility.json_response(data=data)
