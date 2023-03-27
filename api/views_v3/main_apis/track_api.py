"""
    Title: Tracking Api views
    Description: This file will contain all functions for Tracking Api views
    Created: Oct 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from prompt_toolkit.validation import ValidationError

from rest_framework.views import APIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import TrackingStatus, Leg, Shipment
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.track_serializers import TrackSerializer
from api.utilities.utilities import Utility


class TrackingApi(UbbeMixin, APIView):
    """
        Get a List of all tracking, or create a new tracking status for a shipment.
    """
    tracking_response = openapi.Response('Get Shipment Tracking', TrackSerializer(many=True))
    tracking_response_one_response = openapi.Response('Shipment Tracking', TrackSerializer)

    @swagger_auto_schema(
        operation_id='Get All Shipment Tracking',
        operation_description='Get all tracking for shipment.',
        responses={
            '200': tracking_response,
            '400': 'Bad Request'
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get all accounts.
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        shipment_id = self.request.GET.get("shipment_id", "")

        if not shipment_id:
            errors.append({"shipment_id": "Invalid tracking id. Please use ubbe number."})
            return Utility.json_error_response(code="600", message="Track: Invalid tracking id.", errors=errors)

        try:
            shipment = Shipment.objects.prefetch_related(
                Prefetch(
                    'leg_shipment', queryset=Leg.objects.prefetch_related(
                        "tracking_status_leg"
                    )
                )
            ).get(shipment_id=shipment_id)
        except ObjectDoesNotExist:
            errors.append({"shipment_id": "Invalid tracking id. Please use ubbe number or shipment does not exist."})
            return Utility.json_error_response(code="601", message="Track: Invalid tracking id.", errors=errors)

        o_serializer = AddressSerializer(shipment.origin, many=False)
        d_serializer = AddressSerializer(shipment.destination, many=False)

        last = TrackingStatus.objects.filter(leg__shipment=shipment).last()

        ret = {
            "shipment_id": shipment_id,
            "creation_date": shipment.creation_date.isoformat(),
            "estimated_delivery_date": shipment.estimated_delivery_date.isoformat(),
            "reference_one": shipment.reference_one,
            "reference_two": shipment.reference_two,
            "project": shipment.project,
            "origin": o_serializer.data,
            "destination": d_serializer.data,
            "latest_status": last.status,
            "tracking": []
        }

        for leg in shipment.leg_shipment.all():

            if leg.service_code == "PICK_DEL":
                continue

            tracking = leg.tracking_status_leg.all().order_by('updated_datetime')
            last_status = tracking.last()
            serializer = TrackSerializer(tracking, many=True)

            ret["tracking"].append({
                "type": leg.type,
                "leg_id": leg.leg_id,
                "tracking_identifier": leg.tracking_identifier,
                "latest_status": last_status.status,
                "tracking": serializer.data[::-1]
            })

        return Utility.json_response(data=ret)

    @swagger_auto_schema(
        operation_id='Create Tracking Status',
        operation_description='Add a tracking status to a shipment leg.',
        request_body=TrackSerializer,
        responses={
            '200': tracking_response_one_response,
            '400': 'Bad Request'
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new tracking.
            :param request: request
            :return: Json of Tracking.
        """
        errors = []

        json_data = request.data
        serializer = TrackSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="602", message="Track: Invalid values.", errors=serializer.errors
            )

        serializer.validated_data["leg_id"] = json_data["leg_id"]

        try:
            serializer.create(validated_data=serializer.validated_data)
        except (ValidationError, IntegrityError) as e:
            errors.append({"track": f"{str(e)}"})
            return Utility.json_error_response(code="604", message="Track: Failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Update Tracking',
        operation_description='Update individual Tracking in the system.',
        responses={
            '200': tracking_response,
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update Tracking Information.
            :param request: request
            :return: Tracking json.
        """
        errors = []
        json_data = request.data
        serializer = TrackSerializer(data=json_data, many=False)
        tracking_id = json_data.get("tracking_id", -1)

        try:
            tracking = TrackingStatus.objects.get(pk=tracking_id)
        except ObjectDoesNotExist:
            errors.append({"track": f"Tracking not found for {tracking_id}"})
            return Utility.json_error_response(code="605", message="Track: Tracking not found", errors=errors)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="606", message="Track: Invalid values.", errors=serializer.errors
            )

        try:
            serializer.update(instance=tracking, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="607", message="Track: Failed to update.", errors=serializer.errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        serializer.instance = tracking

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Tracking',
        operation_description='Delete individual tracking from the system.',
        responses={
            '200': "Tracking has been deleted.",
            '500': 'Internal Server Error',
            '400': 'Bad Request'
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete Tracking
            :param request: request
            :return: Message indicating Success
        """
        errors = []
        json_data = request.data
        tracking_id = json_data.get("tracking_id", -1)

        try:
            tracking = TrackingStatus.objects.get(pk=tracking_id)
        except ObjectDoesNotExist:
            errors.append({"track": f"Tracking not found for {tracking_id}"})
            return Utility.json_error_response(code="608", message="Track: Tracking not found", errors=errors)

        tracking.delete()

        return Utility.json_response(data={"message": "Tracking has been deleted."})
