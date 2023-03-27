"""
    Title: Celery Tracking Status Change
    Description:
        This file will Trigger Webhook post for Tracking status change behind the scenes, if all conditions pass.
    Created: July 14, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist

from api.serializers_v3.common.track_serializers import TrackSerializer
from api.utilities.webhooks import WebHookEvent

from brain.celery import app


class CeleryTrackStatusChange:
    """
        Trigger Webhook for Tracking status change behind the scenes.
    """

    @app.task(bind=True)
    def tracking_status_change(self, status: int, leg_id: str) -> None:
        """
            Perform webhook event for tracking status change if the sub account has the webhook setup.
            :param status:
            :return: None
        """
        from api.models import TrackingStatus, Webhook

        event = "TSC"

        statuses = TrackingStatus.objects.select_related(
            "leg__shipment__subaccount"
        ).filter(leg__leg_id=leg_id).order_by('-updated_datetime')[:2]

        if statuses.count() < 1:
            return

        latest_status = statuses[0]
        sub_account = latest_status.leg.shipment.subaccount
        data = TrackSerializer(latest_status, many=False).data
        data["leg_id"] = latest_status.leg_id

        try:
            webhook = Webhook.objects.get(sub_account=sub_account, event=event)
        except ObjectDoesNotExist:
            return

        wb = WebHookEvent(data=data, sub_account=sub_account, webhook=webhook)
        wb.send_event()
