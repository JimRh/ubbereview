"""
    Title: Cancel Api Views V3
    Description: This file will contain all functions for Cancel Api views
    Created: Nov 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import DestroyAPIView

from api.apis.cancel.cancel import Cancel
from api.exceptions.project import CancelException
from api.mixins.view_mixins import UbbeMixin
from api.serializers_v3.common.cancel_serializer import CancelSerializer
from api.utilities.utilities import Utility


class CancelApi(UbbeMixin, DestroyAPIView):
    http_method_names = ['post']

    @swagger_auto_schema(
        request_body=CancelSerializer,
        operation_id='Cancel Shipment',
        operation_description='Cancel a shipment or leg by either sending the  "shipment_id" to cancel the full '
                              'shipment or send a "leg_id" to cancel a individual leg of the shipment.',
        responses={
            '200': "Successfully Canceled.",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        errors = []
        json_data = request.data

        if 'shipment_id' not in json_data and 'leg_id' not in json_data:
            errors.append({"fields": "'shipment_id' or 'leg_id' is required."})
            return Utility.json_error_response(
                code="1000", message="Cancel: 'shipment_id' or 'leg_id' is required.", errors=errors
            )
        elif 'shipment_id' in json_data and 'leg_id' in json_data:
            errors.append({"fields": "One of 'shipment_id' and 'leg_id' is required."})
            return Utility.json_error_response(
                code="1001", message="Cancel: One of 'shipment_id' and 'leg_id' is required.", errors=errors
            )

        serializer = CancelSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1002", message="Cancel: Invalid values.", errors=serializer.errors
            )

        try:
            serializer.validated_data["sub_account"] = self._sub_account
            response = Cancel(ubb_request=serializer.validated_data).cancel()
        except CancelException as e:
            errors.append({"fields": f'Cancel failed: {str(e)}'})
            return Utility.json_error_response(code="1003", message="Cancel: Failed.", errors=errors)

        # CeleryEmail.cancel_shipment_email.delay(request=response)

        return Utility.json_response(data=response)
