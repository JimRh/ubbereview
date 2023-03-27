"""
    Title: TrackingStatus Model
    Description: This file will contain functions for TrackingStatus Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from datetime import datetime

from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone

from api.globals.project import DEFAULT_CHAR_LEN, MAX_CHAR_LEN
from api.models.base_table import BaseTable


class TrackingStatus(BaseTable):
    """
        TrackingStatus Model
    """

    leg = ForeignKey("Leg", on_delete=CASCADE, related_name='tracking_status_leg')
    status = CharField(
        max_length=DEFAULT_CHAR_LEN, help_text="The status string provided from the carrier about the leg"
    )
    details = CharField(
        max_length=MAX_CHAR_LEN, blank=True, help_text="Details about the leg provided from the carrier"
    )
    delivered_datetime = DateTimeField(
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc),
        help_text="The datetime the leg was delivered. If the leg is undelivered the datetime defaults to"
                  " 0001-01-01T00:00:00"
    )
    estimated_delivery_datetime = DateTimeField(
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc),
        help_text="The datetime the leg is estimated to be delivered. Provided by the carrier"
    )
    updated_datetime = DateTimeField(
        default=timezone.now,
        help_text="The datetime the status was made."
    )

    class Meta:
        verbose_name = "Tracking Status"
        verbose_name_plural = "Shipment - Tracking Statuses"
        unique_together = ('leg', 'delivered_datetime', 'estimated_delivery_datetime', 'status', 'details')

    @classmethod
    def create(cls, param_dict: dict = None) -> 'TrackingStatus':
        """
            Create TrackingStatus
            :param param_dict: Carrier Markup Fields, described above
            :return: TrackingStatus Object
        """
        status = cls()
        if param_dict is not None:
            status.set_values(param_dict)
            status.leg = param_dict.get("leg")
        return status

    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)
        from api.background_tasks.webhooks.tracking_status_change import CeleryTrackStatusChange

        CeleryTrackStatusChange.tracking_status_change.delay(status=self.pk, leg_id=self.leg.leg_id)

    # Override
    def __repr__(self) -> str:
        return f"< TrackingStatus ({self.leg.leg_id}: {self.status}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.leg.leg_id}: {self.status}"
