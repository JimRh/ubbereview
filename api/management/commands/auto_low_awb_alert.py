"""
    Title: Low Airway Bill Notification System
    Description: The file will check each Carrier for low airway bill counts in ProBillNumber modal. Low = under 20
    Created: July 12, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""


from django.core.management import BaseCommand

from api.emails import Emails
from api.globals.carriers import CAN_NORTH, CALM_AIR, KEEWATIN_AIR, PANORAMA_AIR, PERIMETER_AIR
from api.models import ProBillNumber, Carrier


class Command(BaseCommand):
    _low = 20

    def handle(self, *args, **options) -> None:
        """

            :param args:
            :param options:
            :return:
        """
        low_airwaybills = []
        exclude = [CAN_NORTH, CALM_AIR, KEEWATIN_AIR, PANORAMA_AIR, PERIMETER_AIR]

        air_carriers = Carrier.objects.filter(mode__in=["AI"]).exclude(code__in=exclude)

        for air in air_carriers:

            probill_count = ProBillNumber.objects.filter(carrier__code=air.code).count()

            if probill_count > self._low:
                continue

            # Send email Notification
            low_airwaybills.append({
                "carrier_code": air.code,
                "carrier_name": air.name,
                "remaining": probill_count
            })

        if low_airwaybills:
            Emails.low_airwaybill_email(data={"carriers": low_airwaybills})



