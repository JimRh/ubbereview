"""
    Title: Dangerous Goods Placard api views
    Description: This file will contain all functions for dangerous goods placard api functions.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodPlacard
from api.serializers_v3.private.dangerous_goods.dg_placard_serializers import DGPlacardSerializer
from api.utilities.utilities import Utility


class DangerousGoodPlacardApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good placard queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodPlacard.objects.all()

    @swagger_auto_schema(
        operation_id='Get DG Placards',
        operation_description='Get a list of dangerous good placards.',
        responses={
            '200': openapi.Response('Get DG Placard', DGPlacardSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good placard in the system based on the allowed parameters and search params.
            :return:
        """

        placard = self.get_queryset()
        serializer = DGPlacardSerializer(placard, many=True)

        return Utility.json_response(data=serializer.data)
