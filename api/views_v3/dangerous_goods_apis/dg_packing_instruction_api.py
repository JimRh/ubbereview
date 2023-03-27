"""
    Title: Dangerous Goods Packing Instruction api views
    Description: This file will contain all functions for dangerous goods packing instruction api functions.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodPackingInstruction
from api.serializers_v3.private.dangerous_goods.dg_packing_instruction_serializers import DGPackingInstructionSerializer
from api.utilities.utilities import Utility


class DangerousGoodPackingInstructionApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good packing instruction queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodPackingInstruction.objects.prefetch_related("packaging_types").all()

    @swagger_auto_schema(
        operation_id='Get DG Packing Instructions',
        operation_description='Get a list of dangerous good packing instructions.',
        responses={
            '200': openapi.Response('Get DG Packing Instructions', DGPackingInstructionSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good packing instruction in the system based on the allowed parameters and search params.
            :return:
        """

        packing_instruction = self.get_queryset()
        serializer = DGPackingInstructionSerializer(packing_instruction, many=True)

        return Utility.json_response(data=serializer.data)
