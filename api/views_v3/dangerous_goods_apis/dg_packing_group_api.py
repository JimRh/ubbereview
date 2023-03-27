"""
    Title: Dangerous Goods Packing Group api views
    Description: This file will contain all functions for dangerous goods packing group api functions.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodPackingGroup
from api.serializers_v3.private.dangerous_goods.dg_packing_group_serializer import DGPackingGroupSerializer
from api.utilities.utilities import Utility


class DangerousGoodPackingGroupApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good packing group queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodPackingGroup.objects.all()

    @swagger_auto_schema(
        operation_id='Get DG Packing Group',
        operation_description='Get a list of dangerous good packing group.',
        responses={
            '200': openapi.Response('Get DG Packing Group', DGPackingGroupSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good packing group in the system based on the allowed parameters and search params.
            :return:
        """

        packing_group = self.get_queryset()
        serializer = DGPackingGroupSerializer(packing_group, many=True)

        return Utility.json_response(data=serializer.data)
