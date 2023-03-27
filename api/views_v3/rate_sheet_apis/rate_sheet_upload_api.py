"""
    Title: Rate Sheet api views
    Description: This file will contain all functions for rate sheet api functions.
    Created: November 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ValidationError
from django.db import connection
from drf_yasg.utils import swagger_auto_schema

from rest_framework.generics import CreateAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.serializers_v3.private.rate_sheets.rs_serializers import UploadRateSheetSerializer
from api.utilities.utilities import Utility


class RateSheetUploadApi(UbbeMixin, CreateAPIView):
    http_method_names = ['post']

    @swagger_auto_schema(
        operation_id='Upload Rate Sheet',
        operation_description='Upload excel sheet of rate sheet lanes for a carrier.',
        request_body=UploadRateSheetSerializer,
        responses={
            '200': 'Rate Sheet has been uploaded.',
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Upload carrier excel rate sheet.
            :param request: request
            :return: Rate Sheet Lanes json.
        """
        errors = []
        json_data = request.data
        serializer = UploadRateSheetSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="6400", message="RateSheetUpload: Invalid values.", errors=serializer.errors
            )

        try:
            ret = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="6401", message="RateSheetUpload: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        connection.close()
        return Utility.json_response(data=ret)
