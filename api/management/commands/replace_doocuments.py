import base64
import copy
import datetime
from decimal import Decimal

import requests
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.management import BaseCommand
from django.db import connection, transaction

from api.exceptions.project import RequestError
from api.globals.project import DEFAULT_TIMEOUT_SECONDS, DOCUMENT_TYPE_BILL_OF_LADING
from api.models import Leg, SubAccount, CarrierAccount, ShipDocument
from brain.settings import SKYLINE_BASE_URL


class Command(BaseCommand):

    ubbe_number = [
        "ub6800120672",
        "ub0457816745",
        "ub2270530663",
        "ub2302784920",
        "ub3472139609",
        "ub4214413486",
        "ub1810390327",
        "ub2970031772",
        "ub4253316634",
        "ub3578709507",
        "ub3329196794",
        "ub8927104872",
        "ub1755424649",
        "ub4693016550",
        "ub8230701247",
        "ub3287132972",
        "ub6887865556",
        "ub0756494028",
        "ub8572084192",
        "ub9994855087",
        "ub7988884281",
        "ub3772255407",
        "ub1816795699",
        "ub7675156018",
        "ub2125893235",
        "ub3502332592",
        "ub3206703579",
        "ub5872288928",
        "ub8200064430",
        "ub4155548445",
        "ub1207560232",
        "ub0771705563",
        "ub5531463589",
        "ub9380957186",
        "ub5845407417",
        "ub5559436148",
        "ub6857938051",
        "ub6226390998",
        "ub8771626868"
    ]

    @staticmethod
    def _download_document(document_type: int, awb: str, api_key: str, url: str):
        """
            Make Skyline document call for each of the documents, which includes Cargo labels and airway bill.
        """
        data = {
            'API_Key': api_key,
            'WaybillNumber': awb[-8:]
        }
        try:
            response = requests.post(url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException:
            raise RequestError()

        try:
            response.raise_for_status()
            document = response.content
        except (ValueError, requests.RequestException):
            raise RequestError(response, data)

        encoded = base64.b64encode(document)

        return {
            'document': encoded.decode('ascii'),
            'type': document_type
        }

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        print("**************************** KC TEST ****************************")

        bbe_account = SubAccount.objects.get(subaccount_number="5edcc144-4546-423a-9fcd-2be2418e4720")
        print(bbe_account)
        cn_carrier_account = CarrierAccount.objects.get(subaccount=bbe_account, carrier__code=708)
        print(cn_carrier_account)

        for ubbe in self.ubbe_number:

            print("-------------------------------------------------------------")
            print(ubbe)

            leg = Leg.objects.get(leg_id=f"{ubbe}M")

            print(leg)
            print(leg.tracking_identifier)

            ret = self._download_document(
                document_type=DOCUMENT_TYPE_BILL_OF_LADING,
                awb=leg.tracking_identifier,
                api_key=cn_carrier_account.api_key.decrypt(),
                url=SKYLINE_BASE_URL + '/Reports/Waybill'
            )

            print(ret)

            doc = ShipDocument.objects.get(leg=leg, new_type=DOCUMENT_TYPE_BILL_OF_LADING)

            print(str(doc))

            path = copy.deepcopy(doc.document.path)
            doc.delete()
            default_storage.delete(path)

            ShipDocument.add_document(leg, ret['document'], ret['type'])

