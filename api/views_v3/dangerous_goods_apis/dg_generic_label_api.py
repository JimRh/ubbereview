"""
    Title: Dangerous Goods Generic Label api views
    Description: This file will contain all functions for dangerous goods generic label api functions.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodGenericLabel
from api.serializers_v3.private.dangerous_goods.dg_generic_label_serializer import DGGenericLabelSerializer
from api.utilities.utilities import Utility


class DangerousGoodGenericLabelApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good generic label queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodGenericLabel.objects.all().order_by("name")

    @swagger_auto_schema(
        operation_id='Get DG Generic Labels',
        operation_description='Get a list of dangerous good generic label.',
        responses={
            '200': openapi.Response('Get DG Generic Labels', DGGenericLabelSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good generic label in the system based on the allowed parameters and search params.
            :return:
        """

        generic_label = self.get_queryset()
        serializer = DGGenericLabelSerializer(generic_label, many=True)

        return Utility.json_response(data=serializer.data)
