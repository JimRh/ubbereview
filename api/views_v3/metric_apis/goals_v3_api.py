"""
    Title: Metric Goals api views
    Description: This file will contain all functions for Metric Goals Api.
    Created: Oct 7, 2021
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
from api.models import MetricGoals
from api.serializers_v3.private.metrics.metric_goals import MetricGoalsSerializer
from api.utilities.utilities import Utility


class MetricGoalsApi(UbbeMixin, APIView):
    """
        Get a List of all metric goals, or create a new metric goal.
    """

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'system',
                openapi.IN_QUERY,
                description="ubbe (UB), Fetchable (FE), DeliverEase (DE), or Thrid Party (TP)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'year', openapi.IN_QUERY, description="Example: 2022", type=openapi.TYPE_INTEGER, required=True
            )
        ],
        operation_id='Get Metric Goals',
        operation_description='Get all Metric Goals for a ubbe main account.',
        responses={
            '200': openapi.Response('Get Metric Goals', MetricGoalsSerializer(many=True)),
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get all Metric Goals, Optional Pharam for Filter.
            :param request: request
            :return: Json list of markups.
        """
        errors = []
        system = self.request.GET.get("system")
        year = self.request.GET.get("year")

        if not system:
            errors.append({"system": "Metric Types must be a param. Values: BE, UB, FE, DE, TP"})
            return Utility.json_error_response(code="7000", message="Metric Goal: Not Found.", errors=errors)

        if system not in MetricGoals.SYSTEM_LIST:
            errors.append({"system": "Metric Types must be a param. Values: BE, UB, FE, DE, TP"})
            return Utility.json_error_response(code="7001", message="Metric Goal: Invalid Value.", errors=errors)

        metric_goals = MetricGoals.objects.filter(
            system=system,
            start_date__year=year,
        ).order_by("system", "start_date", "end_date")[::-1]

        serializer = MetricGoalsSerializer(metric_goals, many=True)
        return Utility.json_response(data=serializer.data)

    @staticmethod
    @swagger_auto_schema(
        operation_id='Create Metric Goal',
        operation_description='Create Metric Goal to be used by ubbe main account.',
        request_body=MetricGoalsSerializer,
        responses={
            '200': openapi.Response('Create Metric Goal', MetricGoalsSerializer),
            '400': 'Bad Request'
        },
    )
    def post(request):
        """
            Create a new metric goal.
            :param request: request
            :return: Json of goal.
        """
        errors = []
        json_data = request.data
        serializer = MetricGoalsSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="7002", message="Metric Goal: Invalid values.", errors=serializer.errors
            )

        try:
            goal = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="7003", message="Metric Goal: Failed to save.", errors=errors)

        serializer.instance = goal

        return Utility.json_response(data=serializer.data)


class MetricGoalsDetailApi(UbbeMixin, APIView):
    """
        Get a Metric Goal information or update the information, and delete a goal.
    """

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = MetricGoals.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"pk": "Metric Goal not found."})
            raise ViewException(code="7005", message="Metric Goal: Not found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Metric Goal',
        operation_description='Get individual Metric Goals.',
        responses={
            '200': openapi.Response('Get Metric Goal', MetricGoalsSerializer),
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get individual Metric Goals.
            :param request: request
            :return: Metric Goals json.
        """
        errors = []

        if not self.kwargs.get("pk"):
            errors.append({"pk": "Metric Goal Id Must be a int."})
            return Utility.json_error_response(code="7004", message="Metric Goal: 'pk' is  required.", errors=errors)

        try:
            goal = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer = MetricGoalsSerializer(goal, many=False)
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Update Metric Goal',
        operation_description='Update individual Metric Goal in the system.',
        responses={
            '200': openapi.Response('Update Metric Goal', MetricGoalsSerializer),
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Metric Goal Information.
            :param request: request
            :return: Metric Goal json.
        """
        errors = []
        json_data = request.data
        serializer = MetricGoalsSerializer(data=json_data, many=False)

        if not self.kwargs.get("pk"):
            errors.append({"pk": "Metric Goal Id Must be a int."})
            return Utility.json_error_response(code="7006", message="Metric Goal: 'pk' is  required.", errors=errors)

        try:
            goal = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="7008", message="Metric Goal: Invalid values.", errors=serializer.errors
            )

        try:
            serializer.update(instance=goal, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="7009", message="Metric Goal: failed to update.", errors=errors)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Metric Goal',
        operation_description='Delete individual Metric Goal from the system.',
        responses={
            '200': "Metric Goal has been deleted.",
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete Metric Goal.
            :param request: request
            :return: Message indicating Success
        """

        try:
            goal = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        goal.delete()

        return Utility.json_response(data={"message": "Metric Goal has been deleted."})
