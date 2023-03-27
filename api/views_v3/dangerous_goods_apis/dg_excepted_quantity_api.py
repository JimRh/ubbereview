"""
    Title: Dangerous Goods Excepted Quantity api views
    Description: This file will contain all functions for dangerous goods excepted quantity api functions.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodExceptedQuantity
from api.serializers_v3.private.dangerous_goods.dg_excepted_quantity_serializer import DGExceptedQuantitySerializer
from api.utilities.utilities import Utility


class DangerousGoodExceptedQuantityApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good excepted quantity queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodExceptedQuantity.objects.all()

    @swagger_auto_schema(
        operation_id='Get DG Excepted Quantities',
        operation_description='Get a list of dangerous good excepted quantity.',
        responses={
            '200': openapi.Response('Get DG Excepted Quantities', DGExceptedQuantitySerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good excepted quantity in the system based on the allowed parameters and search params.
            :return:
        """

        classifications = self.get_queryset()
        serializer = DGExceptedQuantitySerializer(classifications, many=True)

        return Utility.json_response(data=serializer.data)
