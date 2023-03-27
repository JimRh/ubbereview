"""
    Title: Dangerous Goods Classifications api views
    Description: This file will contain all functions for dangerous goods classifications api functions.
    Created: November 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListCreateAPIView

from api.mixins.view_mixins import UbbeMixin
from api.models import DangerousGoodClassification
from api.serializers_v3.private.dangerous_goods.dg_classification_serializer import DGClassificationSerializer
from api.utilities.utilities import Utility


class DangerousGoodClassificationApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get']

    def get_queryset(self):
        """
            Get initial dangerous good classification queryset and apply query params to the queryset.
            :return:
        """
        return DangerousGoodClassification.objects.select_related("label").all()

    @swagger_auto_schema(
        operation_id='Get DG Classifications',
        operation_description='Get a list of dangerous good classifications.',
        responses={
            '200': openapi.Response('Get DG Classifications', DGClassificationSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get dangerous good classification in the system based on the allowed parameters and search params.
            :return:
        """

        classifications = self.get_queryset()
        serializer = DGClassificationSerializer(classifications, many=True)

        return Utility.json_response(data=serializer.data)
