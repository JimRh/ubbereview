"""
    Title: Dangerous Goods Packaging Type api views
    Description: This file will contain all functions for dangerous goods packaging type api functions.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodPackagingType
from api.serializers_v3.private.dangerous_goods.dg_packaging_type_serializers import DGPackagingTypeSerializer
from api.utilities.utilities import Utility


class DangerousGoodPackagingTypeApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good packaging type queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodPackagingType.objects.all()

    @swagger_auto_schema(
        operation_id='Get DG Packaging Type',
        operation_description='Get a list of dangerous good packaging type.',
        responses={
            '200': openapi.Response('Get DG Packaging Type', DGPackagingTypeSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good packaging type in the system based on the allowed parameters and search params.
            :return:
        """

        packing_type = self.get_queryset()
        serializer = DGPackagingTypeSerializer(packing_type, many=True)

        return Utility.json_response(data=serializer.data)
