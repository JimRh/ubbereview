"""
    Title: Bill of Lading Apis
    Description: This file will contain all functions for bill of lading api.
    Created: November 16, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import SubAccount, NatureOfGood
from api.utilities.utilities import Utility

# TODO - REDO THIS ENDPOINT AS WE NEED TO CONSOLIDATE FOR A GENERAL ENDPOINT and add serializer.
# TODO - Should this be cached or not.


class NatureOfGoodsApi(UbbeMixin, APIView):

    @swagger_auto_schema(
        operation_id='Get CN NOG',
        operation_description='Get a list of canadian north nature of goods.',
        responses={
            '200': 'list of NOGs...',
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        is_food = self.request.GET.get("is_food", "False") == "True"

        try:
            self.get_sub_account()
        except ViewException as e:
            connection.close()
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        nogs = list(NatureOfGood.objects.filter(
            skyline_account__sub_account=self._sub_account,
            is_food=is_food,
        ).exclude(rate_priority_id__in=[3]).values("nog_id", "nog_description").distinct())

        if not nogs:
            nogs = list(NatureOfGood.objects.filter(
                skyline_account__sub_account__is_default=True,
                is_food=is_food,
            ).exclude(rate_priority_id__in=[3]).values("nog_id", "nog_description").distinct())

        if is_food:
            default = "179"
        else:
            if str(self._sub_account.subaccount_number) == "2c0148a6-69d7-4b22-88ed-231a084d2db9":
                default = "106"
            else:
                default = "302"

        return Utility.json_response(data={"default_nog": default, "nogs": nogs})
