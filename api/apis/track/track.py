"""
    Title: ubbe Auto Track
    Description: This file will contain functions related to Action Express Api.
    Created: June 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta

from django.db import IntegrityError
from django.db.models import QuerySet
from django.utils import timezone

from api.background_tasks.business_central import CeleryBusinessCentral
from api.exceptions.project import ViewException, NoTrackingStatus
from api.globals.carriers import RATE_SHEET_CARRIERS, SEALIFT_CARRIERS, CAN_NORTH
from api.models import Leg, TrackingStatus, CarrierAccount
from api.utilities.carriers import CarrierUtility


class Track:

    def __init__(self, command):
        exclude_carriers = RATE_SHEET_CARRIERS + SEALIFT_CARRIERS
        self._exclude_carriers = list(exclude_carriers)
        self.command = command

    @staticmethod
    def _save_track(leg: Leg, latest_status: dict) -> None:
        """
        Save latest tracking status for leg and set leg to delivered. If Job File exists, delivered job task line.
        :param latest_status: Tracking Status Dict
        :return: None
        """

        if leg.carrier.code == CAN_NORTH:
            return

        try:
            status = TrackingStatus.create(param_dict=latest_status)
            status.save()
        except IntegrityError as e:
            raise ViewException("Tracking already saved.") from e

        if status.status == "Delivered":
            leg.is_delivered = True
            leg.is_overdue = False
            leg.is_pickup_overdue = False
            leg.save()

            if leg.shipment.ff_number:
                CeleryBusinessCentral().deliver_job_file.delay(data={
                    "job_number": leg.shipment.ff_number,
                    "leg_id": leg.leg_id
                })

            leg_count = Leg.objects.filter(shipment=leg.shipment).count()
            delivered_leg = Leg.objects.filter(shipment=leg.shipment, is_delivered=True).count()

            if leg_count == delivered_leg:
                leg.shipment.is_delivered = True
                leg.shipment.save()

    @staticmethod
    def _get_carrier_account(subaccount, carrier):

        try:
            account = CarrierAccount.objects.get(subaccount=subaccount, carrier=carrier)
        except Exception:
            account = CarrierAccount.objects.get(subaccount__is_default=True, carrier=carrier)

        return account

    def _get_all_undelivered_legs(self) -> QuerySet:
        """
        Get all undelivered legs in the last 45 days and exclude any legs that do not need to be
        tracked.
        :return: Leg QuerySet
        """
        today = datetime.now().replace(tzinfo=timezone.utc)
        past_month = today - timedelta(days=45)
        today = today + timedelta(days=1)

        legs = Leg.objects.select_related(
            "shipment__subaccount",
            "carrier",
        ).filter(
            ship_date__range=[past_month, today],
            is_shipped=True,
            is_delivered=False
        ).exclude(
            carrier__code__in=self._exclude_carriers
        ).exclude(
            service_code="PICK_DEL"
        )

        return legs

    def _perform_track(self):
        """

        :return:
        """

        for leg in self._get_all_undelivered_legs():

            account = self._get_carrier_account(
                subaccount=leg.shipment.subaccount, carrier=leg.carrier
            )

            try:
                api = CarrierUtility.get_ship_api(data={
                    "leg": leg,
                    "carrier_id": leg.carrier.code,
                    "service_code": leg.service_code,
                    "objects": {
                        "sub_account": leg.shipment.subaccount,
                        'carrier_accounts': {
                            leg.carrier.code: {
                                'account': account,
                                "carrier": leg.carrier
                            }
                        },
                    }
                })
            except ViewException:
                continue

            try:
                latest_status = api.track()
            except ViewException as e:
                self.command.stderr.write(self.command.style.ERROR(f'Leg {leg.leg_id}: {str(e.message)}'))
                continue
            except NoTrackingStatus as e:
                self.command.stderr.write(self.command.style.ERROR(f'Leg {leg.leg_id}: {str(e)}'))
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f'Leg {leg.leg_id}: {str(e)}'))
                continue

            try:
                self._save_track(leg=leg, latest_status=latest_status)
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f'Leg {leg.leg_id}: {str(e)}'))
                continue

    def track(self):
        """

        :return:
        """

        self._perform_track()
