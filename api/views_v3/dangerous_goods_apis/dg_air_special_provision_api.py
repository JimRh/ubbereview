"""
    Title: Dangerous Goods Air Special Provision api views
    Description: This file will contain all functions for dangerous goods air special provision api functions.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodAirSpecialProvision
from api.serializers_v3.private.dangerous_goods.dg_air_special_provision_serializer import \
    DGAirSpecialProvisionSerializer
from api.utilities.utilities import Utility


class DangerousGoodAirSpecialProvisionApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good air special provision queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodAirSpecialProvision.objects.all().order_by("code")

    @swagger_auto_schema(
        operation_id='Get Air Special Provision',
        operation_description='Get a list of dangerous good air special provision.',
        responses={
            '200': openapi.Response('Get DG Air Special Provision', DGAirSpecialProvisionSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good air special provision in the system based on the allowed parameters and search params.
            :return:
        """

        special_provision = self.get_queryset()
        serializer = DGAirSpecialProvisionSerializer(special_provision, many=True)

        return Utility.json_response(data=serializer.data)
