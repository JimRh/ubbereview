import copy
import datetime

from decimal import Decimal

from django.test import TestCase

from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_ship_v2 import TstCfExpressShip
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

        self.tst_ship = TstCfExpressShip(ubbe_request=self._request)

    def test_build_address(self):
        """
        Test TST Rate address build.
        """

        record = self.tst_ship._build_address(
            elm_type="test", address=self._request["origin"]
        )

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "test")

        self.assertEqual(record[0].tag, "company")
        self.assertEqual(record[0].text, "TESTING INC")

        self.assertEqual(record[1].tag, "contact")
        self.assertEqual(record[1].text, "TESTING INC TWO")

        self.assertEqual(record[2].tag, "phone")
        self.assertEqual(record[2].text, "7809326245")

        self.assertEqual(record[3].tag, "address1")
        self.assertEqual(record[3].text, "140 Thad Johnson Private 7")

        self.assertEqual(record[4].tag, "city")
        self.assertEqual(record[4].text, "Edmonton")

        self.assertEqual(record[5].tag, "country")
        self.assertEqual(record[5].text, "CN")

        self.assertEqual(record[6].tag, "state")
        self.assertEqual(record[6].text, "AB")

        self.assertEqual(record[7].tag, "zip")
        self.assertEqual(record[7].text, "T5T4R7")

    def test_build_address_all_fields(self):
        """
        Test TST Rate address build.
        """
        copied = copy.deepcopy(self._request["origin"])
        copied["address_two"] = "TESTING THREE"
        copied["extension"] = "1234"

        record = self.tst_ship._build_address(elm_type="test", address=copied)

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "test")

        self.assertEqual(record[0].tag, "company")
        self.assertEqual(record[0].text, "TESTING INC")

        self.assertEqual(record[1].tag, "contact")
        self.assertEqual(record[1].text, "TESTING INC TWO")

        self.assertEqual(record[2].tag, "phone")
        self.assertEqual(record[2].text, "7809326245")

        self.assertEqual(record[3].tag, "address1")
        self.assertEqual(record[3].text, "140 Thad Johnson Private 7")

        self.assertEqual(record[4].tag, "city")
        self.assertEqual(record[4].text, "Edmonton")

        self.assertEqual(record[5].tag, "country")
        self.assertEqual(record[5].text, "CN")

        self.assertEqual(record[6].tag, "state")
        self.assertEqual(record[6].text, "AB")

        self.assertEqual(record[7].tag, "zip")
        self.assertEqual(record[7].text, "T5T4R7")

        self.assertEqual(record[8].tag, "address2")
        self.assertEqual(record[8].text, "TESTING THREE")

        self.assertEqual(record[9].tag, "phoneext")
        self.assertEqual(record[9].text, "1234")

    def test_build_bill(self):
        """
        Test TST Rate bill build.
        """

        record = self.tst_ship._build_bill()

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "billto")

        self.assertEqual(record[0].tag, "company")
        self.assertEqual(record[0].text, "BBE Expediting Ltd.")

        self.assertEqual(record[1].tag, "address1")
        self.assertEqual(record[1].text, "1759 - 35 Avenue East")

        self.assertEqual(record[2].tag, "city")
        self.assertEqual(record[2].text, "Edmonton International Airport")

        self.assertEqual(record[3].tag, "state")
        self.assertEqual(record[3].text, "AB")

        self.assertEqual(record[4].tag, "zip")
        self.assertEqual(record[4].text, "T9E0V6")

    def test_build_instructions(self):
        """
        Test TST Ship instructions
        """

        record = self.tst_ship._build_instructions(instructions="Am instructions")

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "si")

        self.assertEqual(record[0].tag, "description")
        self.assertEqual(record[0].text, "Am instructions")

    def test_build_instructions_awb(self):
        """
        Test TST Ship instructions
        """
        copied = copy.deepcopy(self._request)
        copied["air_carrier"] = "Kencar Air"
        copied["awb"] = "518-YEG-1234567"

        record = TstCfExpressShip(ubbe_request=copied)._build_instructions(
            instructions="Am instructions two"
        )

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "si")

        self.assertEqual(record[0].tag, "description")
        self.assertEqual(record[0].text, "Am instructions two")

        self.assertEqual(record[1].tag, "description")
        self.assertEqual(
            record[1].text,
            "Please reference Kencar Air Airway Bill: 518-YEG-1234567 on arrival.",
        )

    def test_build_packages(self):
        """
        Test TST Ship packages
        """

        packages, dimensions = self.tst_ship._build_packages(
            package_list=self._request["packages"]
        )

        self.assertIsInstance(packages, etree._Element)
        self.assertEqual(packages.tag, "shipdetail")

        self.assertIsInstance(packages[0], etree._Element)
        self.assertEqual(packages[0].tag, "line")

        self.assertEqual(packages[0][0].tag, "description1")
        self.assertEqual(packages[0][0].text, "TEST")

        self.assertEqual(packages[0][1].tag, "pkg")
        self.assertEqual(packages[0][1].text, "BOX")

        self.assertEqual(packages[0][2].tag, "pcs")
        self.assertEqual(packages[0][2].text, "1")

        self.assertEqual(packages[0][3].tag, "swgt")
        self.assertEqual(packages[0][3].text, "102")

        self.assertIsInstance(dimensions, etree._Element)
        self.assertEqual(dimensions.tag, "dimensions")

        self.assertEqual(dimensions[0].tag, "qty")
        self.assertEqual(dimensions[0].text, "1")

        self.assertEqual(dimensions[1].tag, "len")
        self.assertEqual(dimensions[1].text, "5")

        self.assertEqual(dimensions[2].tag, "wid")
        self.assertEqual(dimensions[2].text, "5")

        self.assertEqual(dimensions[3].tag, "hgt")
        self.assertEqual(dimensions[3].text, "5")

    def test_build_pickup(self):
        """
        Test TST Ship build pickup
        """

        pickup = {
            "start_time": "08:00",
            "date": datetime.datetime.strptime("2020-05-14", "%Y-%m-%d").date(),
            "end_time": "16:30",
        }

        pickup_date, ready, close = self.tst_ship._build_pickup(pickup=pickup)

        self.assertEqual(pickup_date, "20200514")
        self.assertEqual(ready, "0800")
        self.assertEqual(close, "1630")

    def test_build_pickup_less_start(self):
        """
        Test TST Ship build pickup less start
        """

        pickup = {
            "start_time": "03:00",
            "date": datetime.datetime.strptime("2020-05-14", "%Y-%m-%d").date(),
            "end_time": "16:30",
        }

        pickup_date, ready, close = self.tst_ship._build_pickup(pickup=pickup)

        self.assertEqual(pickup_date, "20200514")
        self.assertEqual(ready, "0800")
        self.assertEqual(close, "1630")

    def test_build_pickup_greater_start(self):
        """
        Test TST Ship build pickup greater starter
        """

        pickup = {
            "date": datetime.datetime.strptime("2020-05-14", "%Y-%m-%d").date(),
            "start_time": "18:00",
            "end_time": "20:30",
        }

        pickup_date, ready, close = self.tst_ship._build_pickup(pickup=pickup)

        self.assertEqual(pickup_date, "20200515")
        self.assertEqual(ready, "0800")
        self.assertEqual(close, "1600")

    def test_build_pickup_less_end(self):
        """
        Test TST Ship build pickup less end
        """

        pickup = {
            "start_time": "10:00",
            "date": datetime.datetime.strptime("2020-05-14", "%Y-%m-%d").date(),
            "end_time": "11:30",
        }

        pickup_date, ready, close = self.tst_ship._build_pickup(pickup=pickup)

        self.assertEqual(pickup_date, "20200514")
        self.assertEqual(ready, "1000")
        self.assertEqual(close, "1200")

    def test_create_rqby(self):
        address = {
            "city": "Edmonton",
            "province": "AB",
            "country": "CA",
            "postal_code": "T9E0V6",
            "company_name": "test",
            "name": "test name",
            "phone": "7778889999",
            "address": "test address",
            "email": "email@email.com",
        }

        record = self.tst_ship._build_rqby(address=address)

        self.assertIsInstance(record, etree._Element)
        self.assertEqual(record.tag, "rqby")

        self.assertEqual(record[0].tag, "email")
        self.assertEqual(record[0].text, "email@email.com")

        self.assertEqual(record[1].tag, "phone")
        self.assertEqual(record[1].text, "7778889999")

        self.assertEqual(record[2].tag, "name")
        self.assertEqual(record[2].text, "test name")
