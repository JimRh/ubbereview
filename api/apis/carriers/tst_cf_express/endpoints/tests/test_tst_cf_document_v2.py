from decimal import Decimal

from django.test import TestCase

from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_bol_v2 import TstCfExpressBOL
from api.apis.carriers.tst_cf_express.endpoints.tst_cf_document_v2 import (
    TstCfExpressDocument,
)
from api.models import Carrier, CarrierAccount, SubAccount, Leg


class TstCfExpressDocumentTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "user",
        "group",
        "account",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "markup",
        "subaccount",
        "encryted_messages",
        "carrier_account",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        carrier = Carrier.objects.get(code=129)
        carrier_cccount = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self._request = {
            "leg": Leg.objects.last(),
            "tracking_number": "1234567890",
            "objects": {
                "sub_account": "",
                "carrier_accounts": {
                    129: {"account": carrier_cccount, "carrier": carrier}
                },
            },
        }

        self.tst_document = TstCfExpressDocument(ubbe_request=self._request)

    def test_build(self):
        """
        Test Add Child element.
        """
        request = self.tst_document._build(document_type="POD")
        self.assertIsInstance(request, etree._Element)
        self.assertEqual(request.tag, "imagerequest")

        self.assertIsInstance(request[5], etree._Element)
        self.assertEqual(request[5].tag, "type")
        self.assertEqual(request[5].text, "POD")

        self.assertIsInstance(request[6], etree._Element)
        self.assertEqual(request[6].tag, "pro")
        self.assertEqual(request[6].text, "1234567890")
