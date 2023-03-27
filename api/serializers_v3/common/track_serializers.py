"""
    Title: Track Serializers
    Description: This file will contain all functions for Track serializers.
    Created: November 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.background_tasks.business_central import CeleryBusinessCentral
from api.exceptions.project import ViewException
from api.globals.carriers import CAN_NORTH
from api.models import TrackingStatus, Leg


class TrackSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrackingStatus
        fields = [
            'id',
            'status',
            'details',
            'delivered_datetime',
            'estimated_delivery_datetime',
            'updated_datetime'
        ]

    def create(self, validated_data):
        """
            Create New Fuel Surcharge.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            leg = Leg.objects.get(leg_id=validated_data["leg_id"])
        except ObjectDoesNotExist :
            errors.append({"shipment": f"'shipment_id' does not exist."})
            raise ViewException(code="609", message=f'Track: Leg not found.', errors=errors)

        del validated_data["leg_id"]

        status = TrackingStatus.create(param_dict=validated_data)
        status.leg = leg
        status.save()

        if status.status == "Delivered":

            if 'delivered_datetime' in validated_data:
                delivered_date = validated_data["delivered_datetime"]
            else:
                delivered_date = datetime.datetime.now()

            if leg.shipment.ff_number and not leg.is_delivered:
                bc_data = copy.deepcopy(validated_data)
                bc_data["job_number"] = leg.shipment.ff_number
                bc_data["leg_id"] = leg.leg_id

                CeleryBusinessCentral().deliver_job_file.delay(data=bc_data)

            leg.delivered_date = delivered_date
            leg.is_delivered = True
            leg.is_pickup_overdue = False
            leg.is_overdue = False
            leg.save()

            if leg.carrier.code == CAN_NORTH and leg.service_code != "PICK_DEL":

                for pd in Leg.objects.filter(shipment=leg.shipment, service_code="PICK_DEL"):
                    pd.is_delivered = True
                    pd.save()

            leg_count = Leg.objects.filter(shipment=leg.shipment).count()
            delivered_leg = Leg.objects.filter(shipment=leg.shipment, is_delivered=True).count()

            if leg_count == delivered_leg:
                leg.shipment.is_delivered = True
                leg.shipment.save()

        self.instance = status
