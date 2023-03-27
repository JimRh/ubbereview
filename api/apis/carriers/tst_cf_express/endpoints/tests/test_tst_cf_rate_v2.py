import copy
from decimal import Decimal

from django.test import TestCase

from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_rate_v2 import TstCfExpressRate
from api.models import Carrier, CarrierAccount, SubAccount


class TstCfExpressApiTests(TestCase):
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
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "pickup": {
                "start_time": "08:00",
                "date": "2020-05-14",
                "end_time": "16:30",
            },
            "origin": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "140 Thad Johnson Private 7",
                "city": "Edmonton",
                "country": "CA",
                "province": "AB",
                "postal_code": "T5T4R7",
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 Thad Johnson Road",
                "city": "Ottawa",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "K1V0R4",
                "province": "ON",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "has_shipping_bays": True,
            },
            "packages": [
                {
                    "width": Decimal("11"),
                    "package_type": "BOX",
                    "quantity": 1,
                    "length": Decimal("11"),
                    "package": 1,
                    "description": "TEST",
                    "height": Decimal("11"),
                    "weight": Decimal("46"),
                    "imperial_length": Decimal("4.33"),
                    "imperial_width": Decimal("4.33"),
                    "imperial_height": Decimal("4.33"),
                    "imperial_weight": Decimal("101.41"),
                    "is_dangerous_good": False,
                    "volume": Decimal("0.001331"),
                    "is_last": True,
                }
            ],
            "reference_one": "SOMEREF TEST",
            "reference_two": "SOMEREF TEST",
            "is_food": False,
            "is_metric": True,
            "bc_fields": {"bc_job_number": "J00034", "bc_username": "SKIP"},
            "total_pieces": Decimal("1"),
            "total_weight": Decimal("46.00"),
            "total_volume": Decimal("1331.00"),
            "total_weight_imperial": Decimal("101.41"),
            "total_volume_imperial": Decimal("0.05"),
            "is_international": False,
            "is_dangerous_shipment": False,
            "objects": {
                "sub_account": "",
                "carrier_accounts": {
                    129: {"account": carrier_cccount, "carrier": carrier}
                },
            },
            "is_bbe": False,
            "api_client_email": "developer@bbex.com",
            "carrier_id": 129,
            "carrier_name": "TST Overland",
            "carrier_email": "developer@bbex.com",
            "service_code": "G1-1125240",
            "dg_service": None,
            "order_number": "ub2490233447M",
            "carrier_options": [],
        }

        self.tst_rate = TstCfExpressRate(ubbe_request=self._request)

    def test_build_address(self):
        """
        Test TST Rate address build.
        """

        address = {
            "city": "city",
            "province": "province",
            "country": "country",
            "postal_code": "postal_code",
        }

        record = self.tst_rate._build_address(key="test", address=address)

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record[0].tag, "zip")
        self.assertEqual(record[0].text, "postal_code")

        self.assertEqual(record[1].tag, "city")
        self.assertEqual(record[1].text, "city")

        self.assertEqual(record[2].tag, "state")
        self.assertEqual(record[2].text, "province")

    def test_build_address_fail(self):
        """
        Test TST Rate address build.
        """

        address = {
            "city": "city",
            "province": "province",
            "country": "country",
            "postal_coe": "postal_code",
        }

        with self.assertRaises(KeyError) as e:
            record = self.tst_rate._build_address(key="test", address=address)

            self.assertEqual("'postal_code'", str(e.exception))

    def test_build_packages(self):
        """
        Test TST Rate package build.
        """

        packages = [
            {
                "quantity": 1,
                "imperial_length": Decimal("10"),
                "imperial_width": Decimal("10"),
                "imperial_height": Decimal("10"),
                "imperial_weight": Decimal("10"),
            }
        ]

        record = self.tst_rate._build_packages(package_list=packages)

        line = record[0]

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(line[0].tag, "weight")
        self.assertEqual(line[0].text, "10")

        # self.assertEqual(line[1].tag, "class")
        # self.assertEqual(line[1].text, "070")

        self.assertEqual(line[1][0].tag, "qty")
        self.assertEqual(line[1][0].text, "1")

        self.assertEqual(line[1][1].tag, "len")
        self.assertEqual(line[1][1].text, "10")

        self.assertEqual(line[1][2].tag, "wid")
        self.assertEqual(line[1][2].text, "10")

        self.assertEqual(line[1][3].tag, "hgt")
        self.assertEqual(line[1][3].text, "10")

    def test_build(self):
        """
        Test Add Child element.
        """
        base = self.tst_rate._build(service_code="ST")
        self.assertIsInstance(base, etree._Element)
        self.assertEqual(base.tag, "raterequest")
