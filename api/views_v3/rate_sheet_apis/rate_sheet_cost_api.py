"""
    Title: Rate Sheet Lane Api views
    Description: This file will contain all functions for rate sheet lane api functions.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import RateSheetLane
from api.serializers_v3.private.rate_sheets.rs_cost_serializers import RateSheetCostSerializer
from api.utilities.utilities import Utility


class RateSheetLaneApi(UbbeMixin, APIView):
    http_method_names = ['get', 'post']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'rate_sheet_id', openapi.IN_QUERY, description="Rate Sheet ID", type=openapi.TYPE_INTEGER, required=True
            )
        ],
        operation_id='Get Rate Sheet Lane Cost',
        operation_description='Get a list of rate sheet lane cost for a lane.',
        responses={
            '200': openapi.Response('Get Rate Sheet Lane Cost', RateSheetCostSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get markups for the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'rate_sheet_id' not in self.request.query_params:
            errors.append({"rate_sheet_cost": "Missing 'rate_sheet_id' parameter."})
            return Utility.json_error_response(
                code="6300", message="RateSheetCost: Missing 'rate_sheet_id' parameter.", errors=errors
            )

        apis = RateSheetLane.objects.select_related(
            "rate_sheet__carrier"
        ).filter(rate_sheet__id=self.request.query_params["rate_sheet_id"])
        serializer = RateSheetCostSerializer(apis, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=RateSheetCostSerializer,
        operation_id='Create Rate Sheet Lane Cost',
        operation_description='Create a rate sheet lane cost for a weight break.',
        responses={
            '200': openapi.Response('Create Rate Sheet Lane Cost', RateSheetCostSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new rate sheet lane cost.
            :param request: request
            :return: Json list of rate sheet lane cost.
        """
        errors = []
        json_data = request.data
        serializer = RateSheetCostSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6301", message="RateSheetCost: Invalid values.", errors=serializer.errors
            )

        try:
            lane_cost = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6302", message="RateSheetCost: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = lane_cost

        return Utility.json_response(data=serializer.data)


class RateSheetLaneDetailApi(UbbeMixin, APIView):
    http_method_names = ['put', 'delete']

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = RateSheetLane.objects.select_related(
                "rate_sheet__carrier"
            ).get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"rate_sheet_cost": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="6305", message="RateSheetCost: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        request_body=RateSheetCostSerializer,
        operation_id='Update Rate Sheet Lane Cost',
        operation_description='Update a rate sheet lane cost.',
        responses={
            '200': openapi.Response('Update Rate Sheet Lane Cost', RateSheetCostSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update rate sheet lane cost information
            :param request: request
            :return: Json of rate sheet lane cost.
        """
        errors = []
        json_data = request.data
        serializer = RateSheetCostSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6304", message="RateSheetCost: Invalid values.", errors=serializer.errors
            )

        try:
            lane_cost = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            lane_cost = serializer.update(instance=lane_cost, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6306", message="RateSheetCost: Failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = lane_cost
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Rate Sheet Lane Cost',
        operation_description='Delete an rate sheet lane cost for a carrier.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete rate sheet cost from the system.
            :param request: request
            :return: Success rate sheet lane cost.
        """

        try:
            lane_cost = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        lane_cost.delete()

        return Utility.json_response(data={"rate_sheet_cost": self.kwargs["pk"], "message": "Successfully Deleted"})
