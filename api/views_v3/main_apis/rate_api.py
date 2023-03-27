"""
    Title: Rate Api views
    Description: This file will contain all functions for Tracking Api views
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy

import gevent
from django.db import connection
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.carriers.bbe.endpoints.bbe_rate_v1 import BBERate
from api.apis.multi_modal.ground_rate import GroundRate
from api.apis.multi_modal.join_rates import JoinRate
from api.apis.multi_modal.mc_ground_rate import MultiCarrierGroundRate
from api.apis.multi_modal.mm_air_rate import MultiModalAirRate
from api.apis.multi_modal.mm_sealift_rate import MultiModalSealiftRate
from api.apis.rate_v3.rate import RateV3
from api.background_tasks.logger import CeleryLogger
from api.background_tasks.rate_logging import CeleryRateLog
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import CarrierService
from api.process_json.process_rate import ProcessRateJson
from api.serializers_v3.public.rate_serializers import RateRequestSerializer
from api.utilities.carriers import CarrierUtility
from api.utilities.rate_api_helper import RateApiHelper
from api.utilities.utilities import Utility


class RateV3Api(UbbeMixin, APIView):
    http_method_names = ['post']

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return RateRequestSerializer
        else:
            return RateRequestSerializer

    @swagger_auto_schema(
        request_body=RateRequestSerializer,
        operation_id='Rate Shipment',
        operation_description='Get rates for the requested data and carriers.',
        responses={
            '200': "Rates",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Get rates for the request data and carriers.
            :return:
        """
        log_data = copy.deepcopy(request.data)
        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2", message="Invalid values in request.", errors=serializer.errors
            )

        try:
            rates = RateV3(
                ubbe_request=serializer.validated_data,
                log_data=log_data,
                sub_account=self._sub_account,
                user=request.user
            ).rate()
        except ViewException as e:
            connection.close()
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        connection.close()
        return Utility.json_response(data=rates)


class RateApi(UbbeMixin, APIView):
    http_method_names = ['post']

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return RateRequestSerializer
        else:
            return RateRequestSerializer

    @swagger_auto_schema(
        request_body=RateRequestSerializer,
        operation_id='Rate Shipment',
        operation_description='Get rates for the requested data and carriers.',
        responses={
            '200': "Rates",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Get rates for the request data and carriers.
            :return:
        """

        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2", message="Invalid values in request.", errors=serializer.errors
            )

        validated = serializer.validated_data
        log_rate = copy.deepcopy(validated)
        log_rate["account_number"] = self._sub_account.subaccount_number

        try:
            ProcessRateJson(gobox_request=validated, user=request.user, sub_account=self._sub_account).clean()
        except ViewException as e:
            connection.close()
            CeleryRateLog.log_rate.delay(rate_request=log_rate, rate_response={}, is_no_rate=True)
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        if not validated["carrier_id"]:
            connection.close()
            CeleryRateLog.log_rate.delay(rate_request=log_rate, rate_response={}, is_no_rate=True)
            return Utility.json_error_response(code="502", message="No available carriers for request", errors=[])

        # Get additional objects that are used in multiple places.
        carrier_accounts = CarrierUtility().get_carrier_accounts(
            sub_account=self._sub_account,
            carrier_list=validated["carrier_id"]
        )

        validated["objects"] = {
            "sub_account": self._sub_account,
            "user": request.user,
            "carrier_accounts": carrier_accounts,
            "air_list": CarrierUtility().get_air(),
            "ltl_list": CarrierUtility().get_ltl(),
            "ftl_list": CarrierUtility().get_ftl(),
            "courier_list": CarrierUtility().get_courier(),
            "sealift_list": CarrierUtility().get_sealift()
        }

        ground_api = GroundRate(gobox_request=validated)
        air_api = MultiModalAirRate(gobox_request=validated)
        sealift_api = MultiModalSealiftRate(gobox_request=validated)
        interline_api = MultiCarrierGroundRate(gobox_request=validated)

        gevent_ground = gevent.Greenlet.spawn(ground_api.rate)
        gevent_air = gevent.Greenlet.spawn(air_api.rate)
        gevent_sealift = gevent.Greenlet.spawn(sealift_api.rate)
        gevent_interline = gevent.Greenlet.spawn(interline_api.rate)

        gevent.joinall([gevent_air, gevent_ground, gevent_sealift])

        try:
            ground_rates = gevent_ground.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 295", message=f"Ground: {str(e.message)}")
            ground_rates = None
            connection.close()
        except Exception as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 295", message=f"Ground: {str(e)}")
            ground_rates = None
            connection.close()

        try:
            air_rates = gevent_air.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 302", message=f"Air: {str(e.message)}")
            air_rates = None
            connection.close()
        except Exception as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 302", message=f"Air: {str(e)}")
            air_rates = None
            connection.close()

        try:
            sealift_rates = gevent_sealift.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 310", message=f"Sealift: {str(e.message)}")
            sealift_rates = None
            connection.close()
        except Exception as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 310", message=f"Sealift: {str(e)}")
            sealift_rates = None
            connection.close()

        try:
            interline_rates = gevent_interline.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 316", message=f"Interline: {str(e.message)}")
            interline_rates = None
            connection.close()
        except Exception as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 316", message=f"Interline: {str(e)}")
            interline_rates = None
            connection.close()

        if not ground_rates and not air_rates and not sealift_rates and not interline_rates:
            bbe_rate = BBERate(ubbe_request=validated).rate(is_quote=True)
            rates = [(None, bbe_rate, None)]

            all_rates = JoinRate(
                air_rates=[],
                sealift_rates=[],
                ground_rates=rates,
                interline_rates=[],
                sub_account=self._sub_account
            ).join_rates()

        else:
            all_rates = JoinRate(
                air_rates=air_rates,
                sealift_rates=sealift_rates,
                ground_rates=ground_rates,
                interline_rates=interline_rates,
                sub_account=self._sub_account
            ).join_rates()

        carriers = all_rates.pop("carriers")
        all_rates["carrier_service_info"] = CarrierService().get_service_information(carriers=carriers)

        CeleryRateLog.log_rate.delay(rate_request=log_rate, rate_response=all_rates)

        connection.close()
        return Utility.json_response(data=all_rates)


class RateUbbeApi(UbbeMixin, APIView):
    http_method_names = ['post']

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return RateRequestSerializer
        else:
            return RateRequestSerializer

    @swagger_auto_schema(
        request_body=RateRequestSerializer,
        operation_id='Get Rates',
        operation_description='Get rates for the requested data and carriers which will return ubbe rates such as '
                              'economy, standard, and express options.',
        responses={
            '200': "ubbe Rates",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Get rates for the request data and carriers.
            :return:
        """

        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="2", message="Invalid values in request.", errors=serializer.errors
            )

        validated = serializer.validated_data
        log_rate = copy.deepcopy(validated)
        log_rate["account_number"] = self._sub_account.subaccount_number

        try:
            ProcessRateJson(gobox_request=validated, user=request.user, sub_account=self._sub_account).clean()
        except ViewException as e:
            connection.close()
            CeleryRateLog.log_rate.delay(rate_request=log_rate, rate_response={}, is_no_rate=True)
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        if not validated["carrier_id"]:
            connection.close()
            CeleryRateLog.log_rate.delay(rate_request=log_rate, rate_response={}, is_no_rate=True)
            return Utility.json_error_response(code="502", message="No available carriers for request", errors=[])

        # Get additional objects that are used in multiple places.
        carrier_accounts = CarrierUtility().get_carrier_accounts(
            sub_account=self._sub_account,
            carrier_list=validated["carrier_id"]
        )

        validated["objects"] = {
            "sub_account": self._sub_account,
            "user": request.user,
            "carrier_accounts": carrier_accounts,
            "air_list": CarrierUtility().get_air(),
            "ltl_list": CarrierUtility().get_ltl(),
            "ftl_list": CarrierUtility().get_ftl(),
            "courier_list": CarrierUtility().get_courier(),
            "sealift_list": CarrierUtility().get_sealift()
        }

        ground_api = GroundRate(gobox_request=validated)
        air_api = MultiModalAirRate(gobox_request=validated)
        sealift_api = MultiModalSealiftRate(gobox_request=validated)
        interline_api = MultiCarrierGroundRate(gobox_request=validated)

        gevent_ground = gevent.Greenlet.spawn(ground_api.rate)
        gevent_air = gevent.Greenlet.spawn(air_api.rate)
        gevent_sealift = gevent.Greenlet.spawn(sealift_api.rate)
        gevent_interline = gevent.Greenlet.spawn(interline_api.rate)

        gevent.joinall([gevent_air, gevent_ground, gevent_sealift])

        try:
            ground_rates = gevent_ground.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 295", message=f"Ground: {str(e.message)}")
            ground_rates = None
            connection.close()

        try:
            air_rates = gevent_air.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 302", message=f"Air: {str(e.message)}")
            air_rates = None
            connection.close()

        try:
            sealift_rates = gevent_sealift.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 310", message=f"Sealift: {str(e.message)}")
            sealift_rates = None
            connection.close()

        try:
            interline_rates = gevent_interline.get()
        except ViewException as e:
            CeleryLogger().l_debug.delay(location="rate_apis.py line: 316", message=f"Interline: {str(e.message)}")
            interline_rates = None
            connection.close()

        if not ground_rates and not air_rates and not sealift_rates and not interline_rates:
            bbe_rate = BBERate(ubbe_request=validated).rate(is_quote=True)
            rates = [(None, bbe_rate, None)]

            all_rates = JoinRate(
                air_rates=[],
                sealift_rates=[],
                ground_rates=rates,
                interline_rates=[],
                sub_account=self._sub_account
            ).join_rates()

        else:
            all_rates = JoinRate(
                air_rates=air_rates,
                sealift_rates=sealift_rates,
                ground_rates=ground_rates,
                interline_rates=interline_rates,
                sub_account=self._sub_account
            ).join_rates()

        response = RateApiHelper().ubbe_rate_format(rates=all_rates["rates"])

        CeleryRateLog.log_rate.delay(rate_request=log_rate, rate_response=all_rates)

        connection.close()
        return Utility.json_response(data=response)
