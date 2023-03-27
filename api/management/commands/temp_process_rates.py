import copy

import openpyxl
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import BaseCommand
from django.db import transaction
from django.db.models.query_utils import Q

from api.apis.rate_v3.rate import RateV3
from api.exceptions.project import ViewException
from api.models import Shipment, Leg, SubAccount
from api.serializers_v3.public.rate_serializers import RateRequestSerializer


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='File to import from')

    @transaction.atomic
    def handle(self, *args, **options) -> None:

        sub_account = SubAccount.objects.get(subaccount_number="5edcc144-4546-423a-9fcd-2be2418e4720")

        book = openpyxl.load_workbook(options["file"], read_only=True, data_only=True)
        sheet = book.active

        for row in sheet.iter_rows():

            if row[0].value == "Origin City":
                continue

            print("-"*40)

            ubbe_request = {
                "origin": {
                    "address": "123 Street",
                    "city": str(row[0].value).strip().lower(),
                    "province": str(row[2].value).strip().upper(),
                    "country": "CA",
                    "postal_code": str(row[1].value).strip().upper(),
                    "has_shipping_bays": True,
                    "is_residential": False
                },
                "destination": {
                    "address": "123 Street",
                    "city": str(row[3].value).strip().lower(),
                    "province": str(row[5].value).strip().upper(),
                    "country": "CA",
                    "postal_code": str(row[4].value).strip().upper(),
                    "has_shipping_bays": True,
                    "is_residential": False
                },
                "packages": [
                    {
                        "units": "0",
                        "width": 44,
                        "height": 44,
                        "length": 44,
                        "nog_id": "302",
                        "weight": 33,
                        "quantity": 1,
                        "is_metric": True,
                        "package_id": 1,
                        "description": "Sams box",
                        "package_type": "BOX",
                        "package_description": "Package"
                    }
                ],
                "is_food": False,
                "is_metric": True,
                "carrier_options": [],
                "carrier_id": [
                    512,
                    601,
                    309,
                    737,
                    511,
                    1,
                    728,
                    308,
                    767,
                    616,
                    20,
                    127,
                    708,
                    307,
                    71,
                    59,
                    90,
                    122,
                    7,
                    43,
                    2,
                    70,
                    55,
                    506,
                    54,
                    507,
                    730,
                    51,
                    502,
                    505,
                    670,
                    58,
                    726,
                    504,
                    306,
                    11,
                    734,
                    510,
                    129,
                    900,
                    904,
                    8,
                    747,
                    523
                ]
            }

            print(f"{str(row[0].value).strip().upper()}-{str(row[1].value).strip().upper()}-{str(row[2].value).strip().upper()}-{str(row[3].value).strip().upper()}-{str(row[4].value).strip().upper()}-{str(row[5].value).strip().upper()}-")

            serializer = RateRequestSerializer(data=ubbe_request, many=False)

            if not serializer.is_valid():
                print("Invalid")
                continue

            try:
                rates = RateV3(
                    ubbe_request=serializer.validated_data,
                    log_data=copy.deepcopy(ubbe_request),
                    sub_account=sub_account,
                    user=sub_account.user
                ).rate()
            except ViewException as e:
                print("Invalid")
                continue

            print(rates)

