"""
    Title: Dangerous Goods Air Cutoff api views
    Description: This file will contain all functions for dangerous goods air cutoff api functions.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodAirCutoff
from api.serializers_v3.private.dangerous_goods.dg_air_cutoff_serializer import DGAirCutoffSerializer
from api.utilities.utilities import Utility


class DangerousGoodAirCutoffApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good air cutoff queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodAirCutoff.objects.select_related("packing_instruction").all()

    @swagger_auto_schema(
        operation_id='Get Air Cutoff',
        operation_description='Get a list of dangerous good air cutoff .',
        responses={
            '200': openapi.Response('Get Air Cutoff', DGAirCutoffSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good air cutoff in the system based on the allowed parameters and search params.
            :return:
        """

        air_cutoff = self.get_queryset()
        serializer = DGAirCutoffSerializer(air_cutoff, many=True)

        return Utility.json_response(data=serializer.data)
