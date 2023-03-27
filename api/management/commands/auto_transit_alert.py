"""
    Title: Transit Alert System
    Description: This file will responsible for checking for shipments that are overdue for pickup or delivery.
    Created: October 19, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.management import BaseCommand

from api.background_tasks.transit_alert import TransitAlert
from api.emails import Emails
from api.models import Leg


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:

        transit_alert = TransitAlert()
        transit_alert.check_for_overdue()

        legs = Leg.objects.filter(is_delivered=False, shipment__is_cancel=False)

        pickup_overdue = legs.filter(is_pickup_overdue=True).count()
        overdue = legs.filter(is_overdue=True).count()

        Emails.overdue_email(context={
            "pickup_overdue": pickup_overdue,
            "overdue": overdue
        })
