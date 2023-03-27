# """
#     Title: Manitoulin Ship Unit Tests
#     Description: Unit Tests for  Manitoulin Ship. Test Everything.
#     Created: January 09, 2023
#     Author: Yusuf
#     Edited By:
#     Edited Date:
# """
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.manitoulin.endpoints.manitoulin_ship import ManitoulinShip
from api.globals.carriers import MANITOULIN
from api.models import SubAccount, Carrier, CarrierAccount, API


class ManitoulinShipTests(TestCase):
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
        carrier = Carrier.objects.get(code=MANITOULIN)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "pickup": {
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date()
            },
            "origin": {
                "address": "1759 35 Ave E",
                "city": "Edmonton International Airport",
                "province": "ON",
                "country": "CA",
                "postal_code": "T9E0V6",
                "is_residential": False,
                "tailgate_pickup": False,
                "flat_deck_pickup": False,
                "inside_pickup": False,
                "drop_off_at_terminal": False,
                "warehouse_pickup": False,
                "company_name": "BBE EXPEDITING LTD",
            },
            "destination": {
                "address": "800 Macleod Trail S.E",
                "city": "CALGARY",
                "province": "AB",
                "country": "CA",
                "postal_code": "T2P2M5",
                "residential_delivery": False,
                "tailgate_delivery": False,
                "flat_deck_delivery": False,
                "inside_delivery": False,
                "dock_pickup": False,
                "company_name": "TEST",
            },
            "packages": [
                {
                    "class_value": "70.00",
                    "quantity": 1,
                    "package_type": "SKID",
                    "description": "A description of my skid",
                    "imperial_weight": Decimal("200"),
                    "weight_unit_value": "KGS",
                    "imperial_length": Decimal("48"),
                    "imperial_width": Decimal("40"),
                    "imperial_height": Decimal("40"),
                    "unit_value": "cm",
                    "is_dangerous_good": False,
                },
                {
                    "class_value": "70.00",
                    "quantity": 2,
                    "package_type": "BOX",
                    "description": "A description of my pallets",
                    "imperial_weight": Decimal("500"),
                    "weight_unit_value": "KG",
                    "imperial_length": Decimal("50"),
                    "imperial_width": Decimal("60"),
                    "imperial_height": Decimal("20"),
                    "unit_value": "CM",
                    "is_dangerous_good": False,
                },
            ],
            "other": {
                "rock_solid_service_guarantee": True,
                "rock_solid_service_value": "A",
                "call_prior_to_delivery": False,
                "off_hour_pickup": False,
                "off_hour_delivery": False,
                "delivery_by_appointment": False,
                "reference_one": "test ref",
            },
            "special_instructions": "test instructions",
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    MANITOULIN: {"account": carrier_account, "carrier": carrier},
                },
            },
            "carrier_options": [],
            "service_code": "LTL|LF3Q761752",
            "order_number": "UB1234567890",
            "is_pickup": True,
        }

        self._manitoulin_ship = ManitoulinShip(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test build address origin.
        """
        ret = self._manitoulin_ship._build_address(
            key="SHIP", address=self.request["origin"]
        )
        expected = {
            "SHIPCODE": "0061861",
            "SHIPNAME": "BBE EXPEDITING LTD",
            "SHIPADDR": "1759 35 Ave E",
            "SHIPCITY": "edmonton international airport",
            "SHIPPROV": "ON",
            "SHIPPC": "T9E0V6",
            "SHIPNAT": "CN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test build address destination.
        """
        ret = self._manitoulin_ship._build_address(
            key="CONS", address=self.request["destination"]
        )
        expected = {
            "CONSCODE": "0061861",
            "CONSNAME": "TEST",
            "CONSADDR": "800 Macleod Trail S.E",
            "CONSCITY": "calgary",
            "CONSPROV": "AB",
            "CONSPC": "T2P2M5",
            "CONSNAT": "CN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_options_none(self):
        """
        Test build options - no options selected
        """
        self.request["carrier_options"] = []
        ret = self._manitoulin_ship._build_options()
        expected = {
            "OTYPE": "BWLD",
            "OPICKUP": "NONE",
            "DTYPE": "BWLD",
            "DDEL": "NONE",
            "HEAT": False,
            "FRESH": False,
            "FROZEN": False,
            "FDPU": False,
            "FDDEL": False,
            "WP": False,
            "WD": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_options(self):
        """
        Test build options
        """
        self.request["carrier_options"] = [1]
        ret = self._manitoulin_ship._build_options()
        expected = {
            "OTYPE": "BWLD",
            "OPICKUP": "NONE",
            "DTYPE": "BWLD",
            "DDEL": "NONE",
            "HEAT": False,
            "FRESH": False,
            "FROZEN": False,
            "FDPU": False,
            "FDDEL": False,
            "WP": False,
            "WD": False,
        }
        self.assertDictEqual(expected, ret)

    def test_build_details(self):
        """
        Test build details
        """

        ret = self._manitoulin_ship._build_details()
        expected = [
            {
                "BOL_ID": "UB1234567890-1",
                "CLASS": "70",
                "PKGCODE": "SK",
                "NUMPCS": 1,
                "DESC": "A description of my skid",
                "WEIGHT": 200,
                "LENGTH": 48,
                "HEIGHT": 40,
                "WIDTH": 40,
                "WGTUNITS": "LBS",
                "DIMUNITS": "IN",
                "DG": False,
                "DGUN": None,
                "DGNAME": None,
                "DGPG": None,
                "DGCLASS": None,
                "COMMENTS": "",
                "DGTECHNM": "",
            },
            {
                "BOL_ID": "UB1234567890-2",
                "CLASS": "70",
                "PKGCODE": "BX",
                "NUMPCS": 2,
                "DESC": "A description of my pallets",
                "WEIGHT": 500,
                "LENGTH": 50,
                "HEIGHT": 20,
                "WIDTH": 60,
                "WGTUNITS": "LBS",
                "DIMUNITS": "IN",
                "DG": False,
                "DGUN": None,
                "DGNAME": None,
                "DGPG": None,
                "DGCLASS": None,
                "COMMENTS": "",
                "DGTECHNM": "",
            },
        ]

        self.assertEqual(expected, ret)

    def test_build_details_dg(self):
        """
        Test build details - dg
        """
        copied = copy.deepcopy(self.request)
        for package in copied["packages"]:
            package["is_dangerious_good"] = True
            package["un_number"] = "1"
            package["proper_shipping_name"] = "test"
            package["packing_group_str"] = "test"
            package["DGCLASS"] = "1"

        ret = self._manitoulin_ship._build_details()
        expected = [
            {
                "BOL_ID": "UB1234567890-1",
                "CLASS": "70",
                "PKGCODE": "SK",
                "NUMPCS": 1,
                "DESC": "A description of my skid",
                "WEIGHT": 200,
                "LENGTH": 48,
                "HEIGHT": 40,
                "WIDTH": 40,
                "WGTUNITS": "LBS",
                "DIMUNITS": "IN",
                "DG": False,
                "DGUN": None,
                "DGNAME": None,
                "DGPG": None,
                "DGCLASS": None,
                "COMMENTS": "",
                "DGTECHNM": "",
            },
            {
                "BOL_ID": "UB1234567890-2",
                "CLASS": "70",
                "PKGCODE": "BX",
                "NUMPCS": 2,
                "DESC": "A description of my pallets",
                "WEIGHT": 500,
                "LENGTH": 50,
                "HEIGHT": 20,
                "WIDTH": 60,
                "WGTUNITS": "LBS",
                "DIMUNITS": "IN",
                "DG": False,
                "DGUN": None,
                "DGNAME": None,
                "DGPG": None,
                "DGCLASS": None,
                "COMMENTS": "",
                "DGTECHNM": "",
            },
        ]

        self.assertEqual(expected, ret)

        def test_build_details_dg_nos(self):
            """
            Test build details - DG NOS.
            """
            copied = copy.deepcopy(self.request)
            copied["packages"] = [
                {
                    "description": "TEST",
                    "package_type": "DRUM",
                    "freight_class": "70.00",
                    "quantity": 1,
                    "length": "48",
                    "width": "48",
                    "height": "48",
                    "weight": "100",
                    "imperial_length": Decimal("48"),
                    "imperial_width": Decimal("48"),
                    "imperial_height": Decimal("48"),
                    "imperial_weight": Decimal("100"),
                    "is_dangerous_good": True,
                    "proper_shipping_name": "My DG",
                    "un_number": 1234,
                    "class_div": "1",
                    "packing_group_str": "III",
                    "is_nos": True,
                    "is_neq": False,
                    "dg_nos_description": "Tech Name",
                }
            ]

            manitoulin_ship = ManitoulinShip(ubbe_request=copied)
            ret = manitoulin_ship._build_details()
            expected = [
                {
                    "BOL_ID": "UB1234567890-1",
                    "CLASS": "70",
                    "PKGCODE": "SK",
                    "NUMPCS": 1,
                    "DESC": "A description of my skid",
                    "WEIGHT": 200,
                    "LENGTH": 48,
                    "HEIGHT": 40,
                    "WIDTH": 40,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                },
                {
                    "BOL_ID": "UB1234567890-2",
                    "CLASS": "70",
                    "PKGCODE": "BX",
                    "NUMPCS": 2,
                    "DESC": "A description of my pallets",
                    "WEIGHT": 500,
                    "LENGTH": 50,
                    "HEIGHT": 20,
                    "WIDTH": 60,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                },
            ]

            self.assertEqual(expected, ret)

    def test_get_pickup_date(self):
        """
        Test pickup date
        """
        ret = self._manitoulin_ship._get_pickup_date()
        expected = "20210812"
        self.assertEqual(expected, ret)

    def test_build_request(self):
        """
        Test build request.
        """
        ret = self._manitoulin_ship._build_request()
        expected = {
            "SCB": "B",
            "TERMS": "T",
            "PUDATE": "20210812",
            "GS": "N",
            "BILLCODE": "0061861",
            "BILLNAME": "BBE Expediting Ltd",
            "BILLADDR": "1759 35 Ave E",
            "BILLCITY": "Edmonton International Airport",
            "BILLPROV": "AB",
            "BILLPC": "T9E0V6",
            "BILLNAT": "CN",
            "STYPE": "LTL Expedited",
            "CONTNAME": "Customer Service",
            "CONTPHONE": "18884206926",
            "PERSONAL": False,
            "ARCHIVED": False,
            "PRONUM": "",
            "BOLNUM": "UB1234567890",
            "PONUM": "UB1234567890",
            "ORDERNUM": "UB1234567890",
            "REFNUM": "",
            "SHIPNUM": "",
            "INSTRUCT": "test instructions",
            "TRACKNUM": "",
            "QTENUM": "LF3Q761752",
            "DECVAL": None,
            "DECVALC": "C",
            "NOTIFY": False,
            "NOTNAME": "",
            "NOTPHONE": "",
            "APPTDEL": False,
            "APPTDATE": None,
            "APPTTIMETYPE": "",
            "APPTTIMESTART": None,
            "APPTTIMEEND": None,
            "EMERGNAME": "",
            "EMERGPHONE": "",
            "ERAPNUMBER": "",
            "ERAPPHONE": "",
            "CARROUT": "",
            "TRANSPOINT": "",
            "PICKUPNUM": "",
            "OFFHOURPU": False,
            "OFFHOURDEL": False,
            "ORIGPRONUM": "",
            "ORIGTERM": None,
            "DESTTERM": None,
            "TMPNAME": "",
            "SHIPCODE": "0061861",
            "SHIPNAME": "BBE EXPEDITING LTD",
            "SHIPADDR": "1759 35 Ave E",
            "SHIPCITY": "edmonton international airport",
            "SHIPPROV": "ON",
            "SHIPPC": "T9E0V6",
            "SHIPNAT": "CN",
            "CONSCODE": "0061861",
            "CONSNAME": "TEST",
            "CONSADDR": "800 Macleod Trail S.E",
            "CONSCITY": "calgary",
            "CONSPROV": "AB",
            "CONSPC": "T2P2M5",
            "CONSNAT": "CN",
            "OTYPE": "BWLD",
            "OPICKUP": "NONE",
            "DTYPE": "BWLD",
            "DDEL": "NONE",
            "HEAT": False,
            "FRESH": False,
            "FROZEN": False,
            "FDPU": False,
            "FDDEL": False,
            "WP": False,
            "WD": False,
            "DETAILS": [
                {
                    "BOL_ID": "UB1234567890-1",
                    "CLASS": "70",
                    "PKGCODE": "SK",
                    "NUMPCS": 1,
                    "DESC": "A description of my skid",
                    "WEIGHT": 200,
                    "LENGTH": 48,
                    "HEIGHT": 40,
                    "WIDTH": 40,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
                {
                    "BOL_ID": "UB1234567890-2",
                    "CLASS": "70",
                    "PKGCODE": "BX",
                    "NUMPCS": 2,
                    "DESC": "A description of my pallets",
                    "WEIGHT": 500,
                    "LENGTH": 50,
                    "HEIGHT": 20,
                    "WIDTH": 60,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
            ],
        }

        self.assertEqual(expected, ret)

    def test_build_request_multiple_package(self):
        """
        Test build request - Multiple Package
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "Test",
                "package_type": "SKID",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100"),
                "is_dangerous_good": False,
            }
        )

        manitoulin_ship = ManitoulinShip(ubbe_request=copied)
        ret = manitoulin_ship._build_request()
        expected = {
            "SCB": "B",
            "TERMS": "T",
            "PUDATE": "20210812",
            "GS": "N",
            "BILLCODE": "0061861",
            "BILLNAME": "BBE Expediting Ltd",
            "BILLADDR": "1759 35 Ave E",
            "BILLCITY": "Edmonton International Airport",
            "BILLPROV": "AB",
            "BILLPC": "T9E0V6",
            "BILLNAT": "CN",
            "STYPE": "LTL Expedited",
            "CONTNAME": "Customer Service",
            "CONTPHONE": "18884206926",
            "PERSONAL": False,
            "ARCHIVED": False,
            "PRONUM": "",
            "BOLNUM": "UB1234567890",
            "PONUM": "UB1234567890",
            "ORDERNUM": "UB1234567890",
            "REFNUM": "",
            "SHIPNUM": "",
            "INSTRUCT": "test instructions",
            "TRACKNUM": "",
            "QTENUM": "LF3Q761752",
            "DECVAL": None,
            "DECVALC": "C",
            "NOTIFY": False,
            "NOTNAME": "",
            "NOTPHONE": "",
            "APPTDEL": False,
            "APPTDATE": None,
            "APPTTIMETYPE": "",
            "APPTTIMESTART": None,
            "APPTTIMEEND": None,
            "EMERGNAME": "",
            "EMERGPHONE": "",
            "ERAPNUMBER": "",
            "ERAPPHONE": "",
            "CARROUT": "",
            "TRANSPOINT": "",
            "PICKUPNUM": "",
            "OFFHOURPU": False,
            "OFFHOURDEL": False,
            "ORIGPRONUM": "",
            "ORIGTERM": None,
            "DESTTERM": None,
            "TMPNAME": "",
            "SHIPCODE": "0061861",
            "SHIPNAME": "BBE EXPEDITING LTD",
            "SHIPADDR": "1759 35 Ave E",
            "SHIPCITY": "edmonton international airport",
            "SHIPPROV": "ON",
            "SHIPPC": "T9E0V6",
            "SHIPNAT": "CN",
            "CONSCODE": "0061861",
            "CONSNAME": "TEST",
            "CONSADDR": "800 Macleod Trail S.E",
            "CONSCITY": "calgary",
            "CONSPROV": "AB",
            "CONSPC": "T2P2M5",
            "CONSNAT": "CN",
            "OTYPE": "BWLD",
            "OPICKUP": "NONE",
            "DTYPE": "BWLD",
            "DDEL": "NONE",
            "HEAT": False,
            "FRESH": False,
            "FROZEN": False,
            "FDPU": False,
            "FDDEL": False,
            "WP": False,
            "WD": False,
            "DETAILS": [
                {
                    "BOL_ID": "UB1234567890-1",
                    "CLASS": "70",
                    "PKGCODE": "SK",
                    "NUMPCS": 1,
                    "DESC": "A description of my skid",
                    "WEIGHT": 200,
                    "LENGTH": 48,
                    "HEIGHT": 40,
                    "WIDTH": 40,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
                {
                    "BOL_ID": "UB1234567890-2",
                    "CLASS": "70",
                    "PKGCODE": "BX",
                    "NUMPCS": 2,
                    "DESC": "A description of my pallets",
                    "WEIGHT": 500,
                    "LENGTH": 50,
                    "HEIGHT": 20,
                    "WIDTH": 60,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
                {
                    "BOL_ID": "UB1234567890-3",
                    "CLASS": "70",
                    "PKGCODE": "SK",
                    "NUMPCS": 1,
                    "DESC": "Test",
                    "WEIGHT": 100,
                    "LENGTH": 48,
                    "HEIGHT": 48,
                    "WIDTH": 48,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
            ],
        }

        self.assertEqual(expected, ret)

    def test_build_request_dg_package(self):
        """
        Test build request - DG Package
        """
        copied = copy.deepcopy(self.request)
        for package in copied["packages"]:
            package["is_dangerious_good"] = True
            package["un_number"] = "1"
            package["proper_shipping_name"] = "test"
            package["packing_group_str"] = "test"
            package["DGCLASS"] = "1"
        manitoulin_ship = ManitoulinShip(ubbe_request=copied)
        ret = manitoulin_ship._build_request()
        expected = {
            "SCB": "B",
            "TERMS": "T",
            "PUDATE": "20210812",
            "GS": "N",
            "BILLCODE": "0061861",
            "BILLNAME": "BBE Expediting Ltd",
            "BILLADDR": "1759 35 Ave E",
            "BILLCITY": "Edmonton International Airport",
            "BILLPROV": "AB",
            "BILLPC": "T9E0V6",
            "BILLNAT": "CN",
            "STYPE": "LTL Expedited",
            "CONTNAME": "Customer Service",
            "CONTPHONE": "18884206926",
            "PERSONAL": False,
            "ARCHIVED": False,
            "PRONUM": "",
            "BOLNUM": "UB1234567890",
            "PONUM": "UB1234567890",
            "ORDERNUM": "UB1234567890",
            "REFNUM": "",
            "SHIPNUM": "",
            "INSTRUCT": "test instructions",
            "TRACKNUM": "",
            "QTENUM": "LF3Q761752",
            "DECVAL": None,
            "DECVALC": "C",
            "NOTIFY": False,
            "NOTNAME": "",
            "NOTPHONE": "",
            "APPTDEL": False,
            "APPTDATE": None,
            "APPTTIMETYPE": "",
            "APPTTIMESTART": None,
            "APPTTIMEEND": None,
            "EMERGNAME": "",
            "EMERGPHONE": "",
            "ERAPNUMBER": "",
            "ERAPPHONE": "",
            "CARROUT": "",
            "TRANSPOINT": "",
            "PICKUPNUM": "",
            "OFFHOURPU": False,
            "OFFHOURDEL": False,
            "ORIGPRONUM": "",
            "ORIGTERM": None,
            "DESTTERM": None,
            "TMPNAME": "",
            "SHIPCODE": "0061861",
            "SHIPNAME": "BBE EXPEDITING LTD",
            "SHIPADDR": "1759 35 Ave E",
            "SHIPCITY": "edmonton international airport",
            "SHIPPROV": "ON",
            "SHIPPC": "T9E0V6",
            "SHIPNAT": "CN",
            "CONSCODE": "0061861",
            "CONSNAME": "TEST",
            "CONSADDR": "800 Macleod Trail S.E",
            "CONSCITY": "calgary",
            "CONSPROV": "AB",
            "CONSPC": "T2P2M5",
            "CONSNAT": "CN",
            "OTYPE": "BWLD",
            "OPICKUP": "NONE",
            "DTYPE": "BWLD",
            "DDEL": "NONE",
            "HEAT": False,
            "FRESH": False,
            "FROZEN": False,
            "FDPU": False,
            "FDDEL": False,
            "WP": False,
            "WD": False,
            "DETAILS": [
                {
                    "BOL_ID": "UB1234567890-1",
                    "CLASS": "70",
                    "PKGCODE": "SK",
                    "NUMPCS": 1,
                    "DESC": "A description of my skid",
                    "WEIGHT": 200,
                    "LENGTH": 48,
                    "HEIGHT": 40,
                    "WIDTH": 40,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
                {
                    "BOL_ID": "UB1234567890-2",
                    "CLASS": "70",
                    "PKGCODE": "BX",
                    "NUMPCS": 2,
                    "DESC": "A description of my pallets",
                    "WEIGHT": 500,
                    "LENGTH": 50,
                    "HEIGHT": 20,
                    "WIDTH": 60,
                    "WGTUNITS": "LBS",
                    "DIMUNITS": "IN",
                    "DG": False,
                    "DGUN": None,
                    "DGNAME": None,
                    "DGPG": None,
                    "DGCLASS": None,
                    "COMMENTS": "",
                    "DGTECHNM": "",
                },
            ],
        }

        self.assertDictEqual(expected, ret)
