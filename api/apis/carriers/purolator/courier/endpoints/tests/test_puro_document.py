"""
    Title: Purolator Document Unit Tests
    Description: Unit Tests for the Purolator Document. Test Everything.
    Created: December 8, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.courier.endpoints.purolator_documents import (
    PurolatorDocument,
)
from api.globals.project import DOCUMENT_TYPE_SHIPPING_LABEL
from api.models import SubAccount, Carrier, CarrierAccount


class PurolatorDocumentTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "user",
        "group",
        "markup",
        "carrier_markups",
        "account",
        "subaccount",
        "encryted_messages",
        "carrier_account",
        "northern_pd",
        "skyline_account",
        "nature_of_goods",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=11)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "order_number": "ub123423432",
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "name": "Kenneth Carmichael",
                "phone": "7809326245",
                "email": "kcarmichael@bbex.com",
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
                "name": "Kenneth Carhael",
                "phone": "7808908614",
                "email": "kcarmichael@bbex.com",
            },
            "packages": [
                {
                    "quantity": 1,
                    "length": "100",
                    "width": "50",
                    "height": "50",
                    "weight": "50",
                    "package_type": "BOX",
                }
            ],
            "commodities": [],
            "pickup": {
                "start_time": "15:30",
                "date": "2020-12-08",
                "end_time": "18:00",
            },
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    11: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self.response = [
            {
                "PIN": {"Value": "7365798086"},
                "DocumentDetails": {
                    "DocumentDetail": [
                        {
                            "DocumentType": "InternationalBillOfLadingThermal",
                            "Description": None,
                            "DocumentStatus": "Completed",
                            "URL": None,
                            "Data": "JVBERi0xLjQKJdP0zOEKMSA",
                        }
                    ]
                },
            }
        ]

        self._puro_doc = PurolatorDocument(ubbe_request=self.request)

    def test_build_format_response(self):
        expected = [
            {
                "document": "JVBERi0xLjQKJdP0zOEKMSA",
                "type": DOCUMENT_TYPE_SHIPPING_LABEL,
            }
        ]

        self._puro_doc._format_response(documents=self.response)

        self.assertListEqual(expected, self._puro_doc._response)

    def test_build_add_commercial_invoice(self):
        puro_doc = PurolatorDocument(ubbe_request=self.request)
        puro_doc._add_commercial_invoice()

        self.assertIsInstance(self._puro_doc._response, list)
        self.assertEqual(1, len(puro_doc._response))
