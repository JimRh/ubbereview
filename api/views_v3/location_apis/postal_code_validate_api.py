"""
    Title: Postal Code Validate Apis
    Description: This file will contain api endpoints that relate to validating postal code details for the request.
    Created: Sept 15, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.location.postal_code_validate import PostalCodeValidate
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.serializers_v3.common.pickup_validate_serializers import PickupValidateSerializer
from api.serializers_v3.common.postal_code_validate_serializers import PostalCodeValidateSerializer
from api.utilities.utilities import Utility


class PostalCodeValidateApi(UbbeMixin, APIView):
    http_method_names = ['post']

    @swagger_auto_schema(
        request_body=PickupValidateSerializer,
        operation_id='Validate Postal Code',
        operation_description='Validate requested postal code, city, and province combination.',
        responses={
            "200": "Postal Code is Valid",
            "400": "Bad Request",
            "500": "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Validate requested postal code, city, and province combination.
            :param request: data
            :return: Message and boolean of success
        """

        json_data = request.data
        serializer = PostalCodeValidateSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="901", message="Postal Code Validate: Invalid values.", errors=serializer.errors
            )

        try:
            PostalCodeValidate(request=serializer.validated_data).validate()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data={"message": "Postal Code is Valid", "success": True})
