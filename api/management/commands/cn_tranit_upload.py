import openpyxl
from django.core.management import BaseCommand
from django.db import transaction

from api.models import TransitTime


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='File to import from')

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        book = openpyxl.load_workbook(options["file"], read_only=True, data_only=True)
        sheet = book.active

        transit_time = []

        for row in sheet.iter_rows():
            if row[0].value == "Origin Code":
                continue

            transit_time.append(TransitTime.create(param_dict={
                "origin": str(row[0].value).strip().upper(),
                "destination": str(row[1].value).strip().upper(),
                "rate_priority_id": int(row[2].value),
                "rate_priority_code": str(row[3].value).strip().upper(),
                "transit_min": int(row[4].value),
                "transit_max": int(row[5].value)
            }))

        TransitTime.objects.bulk_create(transit_time)

        print("Import Successful")
