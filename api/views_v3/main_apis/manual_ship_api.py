"""
    Title: Manual Shipment views
    Description: This file will contain all functions for Manual Shipment Creation.
    Created: September 26, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.manual_shipment.manual_shipment import ManualShipment
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.serializers_v3.private.ship.manual_ship_serializer import PrivateManualShipSerializer
from api.utilities.utilities import Utility


class ManualShipApi(UbbeMixin, APIView):
    http_method_names = ['post']

    @swagger_auto_schema(
        request_body=PrivateManualShipSerializer,
        operation_id='Manual Shipment',
        operation_description='Create Manual Shipment',
        responses={
            '200': "Manual Shipment",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create Manual Shipment.
            :return:
        """
        serializer = PrivateManualShipSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2", message="Invalid values in request.", errors=serializer.errors
            )

        try:
            shipment = ManualShipment(
                request=serializer.validated_data,
                sub_account=self._sub_account,
                user=request.user
            ).create()
        except ViewException as e:
            connection.close()
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        connection.close()
        return Utility.json_response(data=shipment.shipment_id)
