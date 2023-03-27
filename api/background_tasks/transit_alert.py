"""
    Title: Transit Alert System
    Description: This file will contain functions for Transit Alert.
    Created: October 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

import pytz
from django.utils import timezone

from api.models import Shipment, Leg
from api.utilities.date_utility import DateUtility


class TransitAlert:
    _default_date = datetime.datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    _overdue_buffer = 5
    _hour = 13
    _minute = 0

    @staticmethod
    def next_date(leg: Leg, date: datetime.datetime):
        return DateUtility().new_next_business_day(
            country_code=leg.destination.province.country.code,
            prov_code=leg.destination.province.code,
            in_date=date
        )

    def _process_shipments(self, shipments: list) -> None:
        """

            :param shipments:
            :return: None
        """
        today = datetime.datetime.now(tz=pytz.UTC)

        for shipment in shipments:
            start_date = shipment.creation_date

            # Pickup date takes precedence over creation date
            if shipment.requested_pickup_time != self._default_date:
                start_date = shipment.requested_pickup_time

            # Check corresponding legs
            for leg in shipment.leg_shipment.all():
                est_delivery_date = leg.updated_est_delivery_date

                if leg.delivered_date != self._default_date and leg.delivered_date != leg.updated_est_delivery_date:
                    est_delivery_date = leg.delivered_date

                # Move to next leg
                if leg.is_delivered or leg.service_code in ["PICK_DEL"]:
                    start_date = self.next_date(leg=leg, date=est_delivery_date)
                    continue

                # Break out of the loop as leg is not overdue or in transit yet
                if today < start_date:
                    break

                latest_status = leg.tracking_status_leg.last()

                if latest_status.status == "Created" and today > start_date:
                    leg.is_pickup_overdue = True
                    leg.save()
                    break

                leg.is_pickup_overdue = False

                est_delivery = leg.updated_est_delivery_date
                update_est_delivery = self.next_date(
                    leg=leg, date=(start_date + datetime.timedelta(days=leg.transit_days))
                )

                if est_delivery != update_est_delivery and est_delivery < update_est_delivery:
                    est_delivery = update_est_delivery
                    leg.updated_est_delivery_date = update_est_delivery

                buffer_date = est_delivery - datetime.timedelta(hours=self._overdue_buffer)
                if today > est_delivery or today > buffer_date:
                    leg.is_overdue = True

                if latest_status.status in ["DeliveryException", "Undeliverable"]:
                    leg.is_overdue = True

                leg.save()
                start_date = self.next_date(leg=leg, date=est_delivery)

    def check_for_overdue(self) -> None:
        """
            Check shipments for any overdue or about to be overdue for delivery.
            :return:
        """

        shipments = Shipment.objects.prefetch_related(
            "leg_shipment",
            "leg_shipment__destination__province"
        ).filter(is_delivered=False, is_shipped=True)

        self._process_shipments(shipments=shipments)
