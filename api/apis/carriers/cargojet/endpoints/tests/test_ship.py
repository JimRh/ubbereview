"""
    Title: Cargojet Ship Unit Tests
    Description: Unit Tests for the Cargojet Ship. Test Everything.
    Created: Sept 27, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.cargojet.endpoints.cj_ship import CargojetShip
from api.models import SubAccount, Carrier, CarrierAccount


class CJShipTests(TestCase):
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
        "taxes",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=307)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "order_number": "MYORDER",
            "service_code": "N",
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "name": "BBE",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "YEG",
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "name": "Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "YWG",
            },
            "packages": [
                {
                    "quantity": 1,
                    "length": "100",
                    "width": "50",
                    "height": "50",
                    "weight": "50",
                    "package_type": "BOX",
                    "imperial_length": Decimal("4.17"),
                    "imperial_width": Decimal("4.17"),
                    "imperial_height": Decimal("4.17"),
                    "imperial_weight": Decimal("23.37"),
                },
                {
                    "description": "My Awesome Package",
                    "quantity": 1,
                    "length": "28",
                    "width": "21",
                    "height": "33",
                    "weight": "11",
                    "package_type": "ENVELOPE",
                    "imperial_length": Decimal("8.17"),
                    "imperial_width": Decimal("8.17"),
                    "imperial_height": Decimal("8.17"),
                    "imperial_weight": Decimal("43.37"),
                },
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    307: {"account": carrier_account, "carrier": carrier}
                },
            },
            "pickup": {"date": "2021-09-08", "start": "10:00", "end": "16:00"},
        }

        self.cj_ship = CargojetShip(ubbe_request=self.request)

    def test_get_service_name_two_day(self):
        """
        Test Ship - Get Two Days service name.
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "T"
        cj_ship = CargojetShip(ubbe_request=copied)
        ret = cj_ship._get_service_name()
        expected = "Two Days"
        self.assertEqual(expected, ret)

    def test_get_service_name_standby(self):
        """
        Test Ship - Get Standby service name.
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "S"
        cj_ship = CargojetShip(ubbe_request=copied)
        ret = cj_ship._get_service_name()
        expected = "Standby"
        self.assertEqual(expected, ret)

    def test_get_service_name_normal(self):
        """
        Test Ship - Get normal service name.
        """

        ret = self.cj_ship._get_service_name()
        expected = "Normal"
        self.assertEqual(expected, ret)

    def test_build_packages(self):
        """
        Test Ship - Building Packages.
        """

        ret = self.cj_ship._build_packages(service_type="LLI")
        expected = [
            {
                "COMM": "GEN",
                "SRVICE": "LLI",
                "PIECES": 1,
                "SHPLEN": Decimal("4.17"),
                "SHPWID": Decimal("4.17"),
                "SHPHGT": Decimal("4.17"),
                "SHPWGT": Decimal("23.37"),
            },
            {
                "COMM": "MAIL",
                "SRVICE": "LLI",
                "PIECES": 1,
                "SHPLEN": Decimal("8.17"),
                "SHPWID": Decimal("8.17"),
                "SHPHGT": Decimal("8.17"),
                "SHPWGT": Decimal("43.37"),
            },
        ]
        self.assertListEqual(expected, ret)

    def test_build_package_pharma(self):
        """
        Test Ship - Building Packages.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"][0]["package_type"] = "PHCONR"

        cj_ship = CargojetShip(ubbe_request=copied)
        ret = cj_ship._build_packages(service_type="LLI")
        expected = [
            {
                "COMM": "DRUG",
                "SRVICE": "LLI",
                "PIECES": 1,
                "SHPLEN": Decimal("4.17"),
                "SHPWID": Decimal("4.17"),
                "SHPHGT": Decimal("4.17"),
                "SHPWGT": Decimal("23.37"),
            },
            {
                "COMM": "MAIL",
                "SRVICE": "LLI",
                "PIECES": 1,
                "SHPLEN": Decimal("8.17"),
                "SHPWID": Decimal("8.17"),
                "SHPHGT": Decimal("8.17"),
                "SHPWGT": Decimal("43.37"),
            },
        ]
        self.assertListEqual(expected, ret)

    def test_build_package_dg(self):
        """
        Test Ship - Building Packages.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"][0]["is_dangerous_good"] = True

        cj_ship = CargojetShip(ubbe_request=copied)
        ret = cj_ship._build_packages(service_type="LLI")
        expected = [
            {
                "COMM": "DG",
                "SRVICE": "LLI",
                "PIECES": 1,
                "SHPLEN": Decimal("4.17"),
                "SHPWID": Decimal("4.17"),
                "SHPHGT": Decimal("4.17"),
                "SHPWGT": Decimal("23.37"),
            },
            {
                "COMM": "MAIL",
                "SRVICE": "LLI",
                "PIECES": 1,
                "SHPLEN": Decimal("8.17"),
                "SHPWID": Decimal("8.17"),
                "SHPHGT": Decimal("8.17"),
                "SHPWGT": Decimal("43.37"),
            },
        ]
        self.assertListEqual(expected, ret)

    def test_get_shipper_consignee_code_yeg(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YEG")
        expected = "BBEYEG"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yxe(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YXE")
        expected = "BBEYXE"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yqr(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YQR")
        expected = "BBEYQR"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yyz(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YYZ")
        expected = "BBEYYZ"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yhm(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YHM")
        expected = "BBEYHM"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yow(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YOW")
        expected = "BBEYOW"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_ymx(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YMX")
        expected = "BBEYMX"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yhz(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YHZ")
        expected = "BBEYHZ"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yyt(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YYT")
        expected = "BBEYYT"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yqm(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YQM")
        expected = "BBEYQM"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_ywg(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YWG")
        expected = "BBEYWG"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yvr(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YVR")
        expected = "BBEYVR"
        self.assertEqual(expected, ret)

    def test_get_shipper_consignee_code_yyc(self):
        """
        Test Ship - Building Get Shipper or Consignee code for airport location.
        """

        ret = self.cj_ship._get_shipper_consignee_code(airport="YYC")
        expected = "BBEYYC"
        self.assertEqual(expected, ret)

    def test_build_with_no_booking_date(self):
        """
        Test Ship - Building base request.
        """

        ret = self.cj_ship._build()
        expected = {
            "TENDER_ID": "MYORDER",
            "PRTY": "N",
            "ORIG": "YEG",
            "DEST": "YWG",
            "SHIPORIG": "YEG",
            "SHIPDEST": "YWG",
            "CUSCOD": "BBEYZF",
            "SHPCOD": "",
            "SHPNAME": "BBE Ottawa/BBE",
            "SHPADR": "1540 Airport Road",
            "SHPCTY": "Edmonton International Airport",
            "SHPCNT": "CA",
            "CONCOD": "",
            "CONNAME": "BBE Ottawa/Ottawa",
            "CONADR": "1540 Airport Road",
            "CONCTY": "Edmonton",
            "CONCNT": "CA",
            "INBOND": "N",
            "REFNUM": "/",
            "COMINS": "ubbe (BBE Expediting Ltd)",
            "SPEINS": "",
            "BKGUNT": "F3",
            "SHIPPING": [
                {
                    "COMM": "GEN",
                    "SRVICE": "LL",
                    "PIECES": 1,
                    "SHPLEN": Decimal("4.17"),
                    "SHPWID": Decimal("4.17"),
                    "SHPHGT": Decimal("4.17"),
                    "SHPWGT": Decimal("23.37"),
                },
                {
                    "COMM": "MAIL",
                    "SRVICE": "LL",
                    "PIECES": 1,
                    "SHPLEN": Decimal("8.17"),
                    "SHPWID": Decimal("8.17"),
                    "SHPHGT": Decimal("8.17"),
                    "SHPWGT": Decimal("43.37"),
                },
            ],
        }
        del ret["BKGDATE"]
        self.assertDictEqual(expected, ret)

    def test_build_with_booking_date(self):
        """
        Test Ship - Building base request.
        """
        self.cj_ship._ubbe_request["booking_date"] = "2021-10-13"
        ret = self.cj_ship._build()
        expected = {
            "TENDER_ID": "MYORDER",
            "PRTY": "N",
            "ORIG": "YEG",
            "DEST": "YWG",
            "SHIPORIG": "YEG",
            "SHIPDEST": "YWG",
            "CUSCOD": "BBEYZF",
            "SHPCOD": "",
            "SHPNAME": "BBE Ottawa/BBE",
            "SHPADR": "1540 Airport Road",
            "SHPCTY": "Edmonton International Airport",
            "SHPCNT": "CA",
            "CONCOD": "",
            "CONNAME": "BBE Ottawa/Ottawa",
            "CONADR": "1540 Airport Road",
            "CONCTY": "Edmonton",
            "CONCNT": "CA",
            "INBOND": "N",
            "REFNUM": "/",
            "COMINS": "ubbe (BBE Expediting Ltd)",
            "SPEINS": "",
            "BKGUNT": "F3",
            "SHIPPING": [
                {
                    "COMM": "GEN",
                    "SRVICE": "LL",
                    "PIECES": 1,
                    "SHPLEN": Decimal("4.17"),
                    "SHPWID": Decimal("4.17"),
                    "SHPHGT": Decimal("4.17"),
                    "SHPWGT": Decimal("23.37"),
                },
                {
                    "COMM": "MAIL",
                    "SRVICE": "LL",
                    "PIECES": 1,
                    "SHPLEN": Decimal("8.17"),
                    "SHPWID": Decimal("8.17"),
                    "SHPHGT": Decimal("8.17"),
                    "SHPWGT": Decimal("43.37"),
                },
            ],
        }
        del ret["BKGDATE"]
        self.assertDictEqual(expected, ret)
