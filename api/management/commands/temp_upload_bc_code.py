import openpyxl
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import BaseCommand
from django.db import transaction
from django.db.models.query_utils import Q

from api.models import Shipment, Leg, SubAccount


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='File to import from')

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        book = openpyxl.load_workbook(options["file"], read_only=True, data_only=True)
        sheet = book.active

        for row in sheet.iter_rows():

            if row[0].value == "Job Name":
                continue

            job_number = str(row[1].value).strip()
            job_task_no = str(row[2].value).strip().lower()
            tracking = str(row[4].value).strip()
            bc_customer_code = str(row[7].value).strip()
            bc_customer_name = str(row[8].value).strip()

            print("-----------------------")
            print(f"{job_number} - {job_task_no} - {job_task_no[:-1]} - {tracking} - {bc_customer_code} - {bc_customer_name}")

            try:
                shipment = Shipment.objects.get(shipment_id=job_task_no[:-1])
            except ObjectDoesNotExist:

                try:
                    leg = Leg.objects.get(tracking_identifier=tracking)
                    shipment = leg.shipment
                except ObjectDoesNotExist:
                    print("continued")
                    continue
                except MultipleObjectsReturned:
                    print("continued - Multi")
                    continue

            if not shipment or (shipment.bc_customer_name and shipment.bc_customer_code):
                continue

            shipment.bc_customer_name = bc_customer_name
            shipment.bc_customer_code = bc_customer_code
            shipment.save()
            print("Done")

        print("Import Successful")
