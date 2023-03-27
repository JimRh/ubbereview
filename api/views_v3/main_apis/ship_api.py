"""
    Title: Ship Api views
    Description: This file will contain all functions for ship Api views
    Created: November 26, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Prefetch
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView

from api.apis.business_central.business_central import BusinessCentral
from api.apis.multi_modal.ship.next_leg_ship import ShipNextLeg
from api.apis.multi_modal.ship.ship import MultiModelShip
from api.background_tasks.business_central import CeleryBusinessCentral
from api.background_tasks.emails import CeleryEmail
from api.background_tasks.logger import CeleryLogger
from api.background_tasks.rate_logging import CeleryRateLog
from api.exceptions.project import ViewException, ShipNextException
from api.globals.project import NEW_FILE, UPDATE_FILE
from api.mixins.view_mixins import UbbeMixin
from api.models import SubAccount, CarrierAccount, API
from api.process_json.process_ship import ProcessShipJson
from api.serializers_v3.private.ship.ship_serializer import PrivateShipRequestSerializer, PrivateShipResponseSerializer
from api.serializers_v3.public.ship_serializers import ShipPublicRequestSerializer, ShipResponseSerializer, ShipAccountRequestSerializer

from api.utilities import utilities
from api.utilities.carriers import CarrierUtility
from api.utilities.utilities import Utility


class ShipApi(UbbeMixin, APIView):
    http_method_names = ['post']

    def get_serializer_class(self):
        """
            Get Serializer instance based on the account caller, BBE users get admin response and all other customers
            get base response.
            :return:
        """
        if self._sub_account.is_bbe:
            return PrivateShipRequestSerializer
        elif self._sub_account.tier.code != "public":
            return ShipAccountRequestSerializer
        else:
            return ShipPublicRequestSerializer

    @swagger_auto_schema(
        operation_id='Ship Shipment',
        operation_description='Perform ship for requested services and carriers.',
        responses={
            '200': openapi.Response('Ship Shipment', ShipPublicRequestSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Perform ship for requested services and carriers.
            :return:
        """

        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(code="", message="Invalid values", errors=serializer.errors)

        json_data = serializer.validated_data
        account_number = json_data.get("account_number", self.request.headers.get("ubbe-account", ""))

        try:
            sub_account = SubAccount.objects.select_related(
                "markup", "client_account", "contact"
            ).prefetch_related(
                Prefetch(
                    "carrieraccount_subaccount", queryset=CarrierAccount.objects.select_related(
                        "carrier", 'api_key', 'username', 'password', 'account_number', 'contract_number',
                    )
                )
            ).get(subaccount_number=account_number)
        except ObjectDoesNotExist:
            errors = [{"ubbe-account": "'ubbe-account' must be in headers."}]
            return Utility.json_error_response(code="", message="'ubbe-account' must be in headers.", errors=errors)

        try:
            ProcessShipJson(gobox_request=json_data, user=request.user, sub_account=sub_account).clean()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        carrier_accounts, carriers = CarrierUtility().get_carrier_accounts_ship(
            sub_account=sub_account,
            gobox_request=json_data
        )

        json_data["objects"] = {
            "sub_account": sub_account,
            "user": request.user,
            "carrier_accounts": carrier_accounts,
            # "air_list": CarrierUtility().get_air(),
            # "ltl_list": CarrierUtility().get_ltl(),
            # "ftl_list": CarrierUtility().get_ftl(),
            # "courier_list": CarrierUtility().get_courier(),
            "sealift_list": CarrierUtility().get_sealift()
        }
        json_data["objects"].update(carriers)
        json_data["is_bbe"] = self._sub_account.is_bbe

        # TODO - NO IDEA WHY THIS IS HERE?
        if json_data["service"]["carrier_id"] in json_data["objects"]["sealift_list"]:
            json_data["objects"]["sailing"] = json_data.pop("sailing")

        try:
            response, shipment = MultiModelShip(gobox_request=json_data).ship()
        except ViewException as e:
            CeleryLogger().l_critical.delay(location="ship_apis.py line: 96", message=str(e.message))
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        CeleryRateLog.log_rate_selected_response.delay(
            rate_log_id=request.data.get("rate_id", ""), ship_request=request.data, shipment_id=shipment.shipment_id
        )

        if self._sub_account.is_bbe:
            response_serializer = PrivateShipResponseSerializer
        else:
            response_serializer = ShipResponseSerializer

        try:
            if API.objects.get(name="BusinessCentral").active and request.user.username in ["gobox", "GoBox", "test"]:
                if "bc_fields" not in json_data:
                    bc_fields = {
                        "bc_username": "Account",
                    }
                else:
                    bc_fields = json_data["bc_fields"]

                bc_type = bc_fields.get("bc_type", 3)

                if bc_type == 2 or not sub_account.is_bc_push:
                    # SKIP Business Central Logic
                    ret = response_serializer(shipment, many=False)
                    CeleryEmail.confirmation_email.delay(data=ret.data, email=shipment.email)

                    return Utility.json_response(data=ret.data)

                bc_fields["is_dangerous_shipment"] = shipment.is_dangerous_good
                bc_fields["shipment_id"] = shipment.shipment_id

                if bc_type == 0:
                    # Create New File
                    job_file = BusinessCentral().create_job_file(data=bc_fields, shipment=shipment)
                    response["ff_file_number"] = job_file
                elif bc_type == 1:
                    # Update Existing Job File
                    response["ff_file_number"] = bc_fields["bc_job_number"]
                    shipment.ff_number = bc_fields["bc_job_number"]
                    shipment.save()
                    CeleryBusinessCentral().update_job_file.delay(data=bc_fields)
                elif sub_account.bc_type == UPDATE_FILE:
                    # Only should be Non BBE Accounts: IE: Raytheon
                    shipment.ff_number = sub_account.bc_job_number
                    shipment.save()

                    response["ff_file_number"] = sub_account.bc_job_number
                    bc_fields["bc_job_number"] = sub_account.bc_job_number

                    CeleryBusinessCentral().update_account_ff_file.delay(data=bc_fields)
                elif sub_account.bc_type == NEW_FILE:
                    job_file = BusinessCentral().create_account_file(data=bc_fields, shipment=shipment)
                    response["ff_file_number"] = job_file
                    shipment.ff_number = job_file
                    shipment.save()

        except Exception as e:
            CeleryLogger().l_critical.delay(location="ship_apis.py line: 96", message=str(e))
            ret = response_serializer(shipment, many=False)
            CeleryEmail.confirmation_email.delay(data=ret.data, email=shipment.email)
            return Utility.json_response(data=ret.data)

        connection.close()
        ret = response_serializer(shipment, many=False)
        CeleryEmail.confirmation_email.delay(data=ret.data, email=shipment.email)

        return Utility.json_response(data=ret.data)


class NextLegPush(UbbeMixin, APIView):

    # Todo - Temporary api

    @swagger_auto_schema(
        operation_id='Ship Next Leg',
        operation_description='Perform ship next leg.',
        responses={
            '200': openapi.Response('Ship Next Leg', ShipPublicRequestSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request):
        json_data = request.data

        ship_id = json_data.get("shipment_id")
        booking_id = json_data.get("booking_number", "")

        if not ship_id:
            errors = [{"shipment_id": f"'shipment_id' is a required field."}]
            return Utility.json_error_response(
                code="4708", message="Dangerous Good: Missing 'shipment_id' field", errors=errors
            )

        try:
            response = ShipNextLeg(shipment_id=ship_id, user=request.user, booking_id=booking_id).ship_next_leg()
        except ShipNextException as err:
            errors = [{"message": err.message}]
            return Utility.json_error_response(
                code="4708", message="Dangerous Good: Failed", errors=errors
            )

        return Utility.json_response(data=response)
