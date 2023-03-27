import openpyxl
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db import transaction

from api.models import ProBillNumber, Carrier


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('carrier_id', type=int, help='Carrier ID number')
        parser.add_argument('file', type=str, help='File to import from')

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        book = openpyxl.load_workbook(options["file"], read_only=True, data_only=True)
        sheet = book.active

        try:
            carrier = Carrier.objects.get(code=options["carrier_id"])
        except ObjectDoesNotExist:
            print(f"Carrier {options['carrier_id']} does not exist in db")
            return None

        probils = []

        for row in sheet.iter_rows():
            if row[0].value == "AWB":
                continue

            probils.append(ProBillNumber(carrier=carrier, probill_number=row[0].value))

        ProBillNumber.objects.bulk_create(probils)

        print("Import Successful")
