"""
    Title: ABF Ship Unit Tests
    Description: Unit Tests for the ABF Ship. Test Everything.
    Created: June 27, 2022
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

import xmltodict
from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.abf_freight.endpoints.abf_ship import ABFShip
from api.exceptions.project import ShipException
from api.globals.carriers import ABF_FREIGHT
from api.models import SubAccount, Carrier, CarrierAccount, API


class ABFShipTests(TestCase):
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
        carrier = Carrier.objects.get(code=ABF_FREIGHT)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "name": "BBE",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "is_residential": False,
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "city": "Ottawa",
                "company_name": "BBE Ottawa",
                "name": "BBE",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "country": "CA",
                "postal_code": "K1V0R1",
                "province": "ON",
                "has_shipping_bays": True,
                "is_residential": False,
            },
            "pickup": {
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "packages": [
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
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    ABF_FREIGHT: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
            "service_code": "LTL|LF3Q761752",
            "order_number": "UB1234567890",
        }

        self.response = xmltodict.parse(
            xml_input='<?xml version="1.0"?><ABF><DOCUMENT>http://www.abfs.com/work/bol/ABF3e48b148.pdf</DOCUMENT><LABELDOCUMENT>http://www.abfs.com/work/labels/LBL3e48b966.pdf</LABELDOCUMENT><PROLABELDOCUMENT></PROLABELDOCUMENT><PRONUMBER>001980689</PRONUMBER><BOLNUMBER></BOLNUMBER><NUMWARNINGS>0</NUMWARNINGS><NUMERRORS>0</NUMERRORS></ABF>'
        )
        self._abf_ship = ABFShip(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test build address origin.
        """
        ret = self._abf_ship._build_address(
            key="Ship", address=self.request["origin"], is_full=True
        )
        expected = {
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ShipName": "BBE Ottawa",
            "ShipContact": "BBE",
            "ShipNamePlus": "BBE",
            "ShipPhone": "7809326245",
            "ShipEmail": "customerservice@ubbe.com",
            "ShipAddress": "1540 Airport Road",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test build address destination.
        """
        ret = self._abf_ship._build_address(
            key="Cons", address=self.request["destination"], is_full=True
        )
        expected = {
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "ConsName": "BBE Ottawa",
            "ConsContact": "BBE",
            "ConsNamePlus": "BBE",
            "ConsPhone": "7809326245",
            "ConsEmail": "customerservice@ubbe.com",
            "ConsAddress": "140 THAD JOHNSON PRIV Suite 7",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_third_party(self):
        """
        Test build address third party.
        """
        ret = self._abf_ship._build_third_party()
        expected = {
            "TPBCity": "edmonton international airport",
            "TPBState": "AB",
            "TPBCountry": "CA",
            "TPBZip": "T9E0V6",
            "TPBName": "BBE Expediting",
            "TPBContact": "Customer Service",
            "TPBNamePlus": "Customer Service",
            "TPBPhone": "18884206926",
            "TPBEmail": "customerservice@ubbe.com",
            "TPBAddress": "1759 35 Ave E",
        }
        self.assertDictEqual(expected, ret)

    def test_build_document_settings(self):
        """
        Test build address third party.
        """
        ret = self._abf_ship._build_document_settings()
        expected = {
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
        }
        self.assertDictEqual(expected, ret)

    def test_build_requester_information(self):
        """
        Test build address third party.
        """
        ret = self._abf_ship._build_requester_information()
        expected = {
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages(self):
        """
        Test build packages.
        """
        ret = self._abf_ship._build_packages()
        expected = {
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "SKD",
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages_multiple(self):
        """
        Test build packages - DG Multiple.
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
        abf_ship = ABFShip(ubbe_request=copied)

        ret = abf_ship._build_packages()
        expected = {
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "SKD",
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "HN2": 1,
            "HT2": "SKD",
            "Desc2": "Test",
            "PN2": 1,
            "PT2": "SKD",
            "FrtLng2": Decimal("48"),
            "FrtWdth2": Decimal("48"),
            "FrtHght2": Decimal("48"),
            "WT2": Decimal("100"),
            "CL2": 70,
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages_dg(self):
        """
        Test build packages - DG.
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
                "is_nos": False,
                "is_neq": False,
            }
        ]

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_packages()
        expected = {
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "DR",
            "Desc1": "TEST",
            "PN1": 1,
            "PT1": "DR",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "HZ1": "Y",
            "HZUN1": 1234,
            "HZCL1": "1",
            "HZPropName1": "My DG",
            "HZPackGrp1": "III",
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages_dg_nos(self):
        """
        Test build packages - DG NOS.
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

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_packages()
        expected = {
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "DR",
            "Desc1": "TEST",
            "PN1": 1,
            "PT1": "DR",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "HZ1": "Y",
            "HZUN1": 1234,
            "HZCL1": "1",
            "HZPropName1": "My DG",
            "HZPackGrp1": "III",
            "HZTechName1": "Tech Name",
        }
        self.assertDictEqual(expected, ret)

    def test_build_reference_numbers(self):
        """
        Test build reference numbers.
        """
        ret = self._abf_ship._build_reference_numbers()
        expected = {"Bol": "UB1234567890", "PO1": "", "PO2": ""}
        self.assertDictEqual(expected, ret)

    def test_build_reference_numbers_ref_one(self):
        """
        Test build reference numbers - Shipment ID + Ref One
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Ref One"

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_reference_numbers()
        expected = {"Bol": "UB1234567890", "PO1": "Ref One", "PO2": ""}
        self.assertDictEqual(expected, ret)

    def test_build_reference_numbers_ref_two(self):
        """
        Test build reference numbers - Shipment ID + Ref Two
        """
        copied = copy.deepcopy(self.request)
        copied["reference_two"] = "Ref Two"

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_reference_numbers()
        expected = {"Bol": "UB1234567890", "PO1": "", "PO2": "Ref Two"}
        self.assertDictEqual(expected, ret)

    def test_build_reference_numbers_all(self):
        """
        Test build reference numbers - Shipment ID + Ref Two
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Ref One"
        copied["reference_two"] = "Ref Two"

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_reference_numbers()
        expected = {"Bol": "UB1234567890", "PO1": "Ref One", "PO2": "Ref Two"}
        self.assertDictEqual(expected, ret)

    def test_build_request(self):
        """
        Test build request.
        """
        ret = self._abf_ship._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "QuoteID": "LF3Q761752",
            "RequesterType": "3",
            "PayTerms": "P",
            "ProAutoAssign": "Y",
            "Instructions": "",
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ShipName": "BBE Ottawa",
            "ShipContact": "BBE",
            "ShipNamePlus": "BBE",
            "ShipPhone": "7809326245",
            "ShipEmail": "customerservice@ubbe.com",
            "ShipAddress": "1540 Airport Road",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "ConsName": "BBE Ottawa",
            "ConsContact": "BBE",
            "ConsNamePlus": "BBE",
            "ConsPhone": "7809326245",
            "ConsEmail": "customerservice@ubbe.com",
            "ConsAddress": "140 THAD JOHNSON PRIV Suite 7",
            "TPBCity": "edmonton international airport",
            "TPBState": "AB",
            "TPBCountry": "CA",
            "TPBZip": "T9E0V6",
            "TPBName": "BBE Expediting",
            "TPBContact": "Customer Service",
            "TPBNamePlus": "Customer Service",
            "TPBPhone": "18884206926",
            "TPBEmail": "customerservice@ubbe.com",
            "TPBAddress": "1759 35 Ave E",
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "SKD",
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
        }
        self.assertDictEqual(expected, ret)

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

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "QuoteID": "LF3Q761752",
            "RequesterType": "3",
            "PayTerms": "P",
            "ProAutoAssign": "Y",
            "Instructions": "",
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ShipName": "BBE Ottawa",
            "ShipContact": "BBE",
            "ShipNamePlus": "BBE",
            "ShipPhone": "7809326245",
            "ShipEmail": "customerservice@ubbe.com",
            "ShipAddress": "1540 Airport Road",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "ConsName": "BBE Ottawa",
            "ConsContact": "BBE",
            "ConsNamePlus": "BBE",
            "ConsPhone": "7809326245",
            "ConsEmail": "customerservice@ubbe.com",
            "ConsAddress": "140 THAD JOHNSON PRIV Suite 7",
            "TPBCity": "edmonton international airport",
            "TPBState": "AB",
            "TPBCountry": "CA",
            "TPBZip": "T9E0V6",
            "TPBName": "BBE Expediting",
            "TPBContact": "Customer Service",
            "TPBNamePlus": "Customer Service",
            "TPBPhone": "18884206926",
            "TPBEmail": "customerservice@ubbe.com",
            "TPBAddress": "1759 35 Ave E",
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "SKD",
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "HN2": 1,
            "HT2": "SKD",
            "Desc2": "Test",
            "PN2": 1,
            "PT2": "SKD",
            "FrtLng2": Decimal("48"),
            "FrtWdth2": Decimal("48"),
            "FrtHght2": Decimal("48"),
            "WT2": Decimal("100"),
            "CL2": 70,
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_dg_package(self):
        """
        Test build request - DG Package
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

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "QuoteID": "LF3Q761752",
            "RequesterType": "3",
            "PayTerms": "P",
            "ProAutoAssign": "Y",
            "Instructions": "",
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ShipName": "BBE Ottawa",
            "ShipContact": "BBE",
            "ShipNamePlus": "BBE",
            "ShipPhone": "7809326245",
            "ShipEmail": "customerservice@ubbe.com",
            "ShipAddress": "1540 Airport Road",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "ConsName": "BBE Ottawa",
            "ConsContact": "BBE",
            "ConsNamePlus": "BBE",
            "ConsPhone": "7809326245",
            "ConsEmail": "customerservice@ubbe.com",
            "ConsAddress": "140 THAD JOHNSON PRIV Suite 7",
            "TPBCity": "edmonton international airport",
            "TPBState": "AB",
            "TPBCountry": "CA",
            "TPBZip": "T9E0V6",
            "TPBName": "BBE Expediting",
            "TPBContact": "Customer Service",
            "TPBNamePlus": "Customer Service",
            "TPBPhone": "18884206926",
            "TPBEmail": "customerservice@ubbe.com",
            "TPBAddress": "1759 35 Ave E",
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "DR",
            "Desc1": "TEST",
            "PN1": 1,
            "PT1": "DR",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "HZ1": "Y",
            "HZUN1": 1234,
            "HZCL1": "1",
            "HZPropName1": "My DG",
            "HZPackGrp1": "III",
            "HZTechName1": "Tech Name",
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_references(self):
        """
        Test build request - References
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Ref One"
        copied["reference_two"] = "Ref Two"

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "QuoteID": "LF3Q761752",
            "RequesterType": "3",
            "PayTerms": "P",
            "ProAutoAssign": "Y",
            "Instructions": "",
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ShipName": "BBE Ottawa",
            "ShipContact": "BBE",
            "ShipNamePlus": "BBE",
            "ShipPhone": "7809326245",
            "ShipEmail": "customerservice@ubbe.com",
            "ShipAddress": "1540 Airport Road",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "ConsName": "BBE Ottawa",
            "ConsContact": "BBE",
            "ConsNamePlus": "BBE",
            "ConsPhone": "7809326245",
            "ConsEmail": "customerservice@ubbe.com",
            "ConsAddress": "140 THAD JOHNSON PRIV Suite 7",
            "TPBCity": "edmonton international airport",
            "TPBState": "AB",
            "TPBCountry": "CA",
            "TPBZip": "T9E0V6",
            "TPBName": "BBE Expediting",
            "TPBContact": "Customer Service",
            "TPBNamePlus": "Customer Service",
            "TPBPhone": "18884206926",
            "TPBEmail": "customerservice@ubbe.com",
            "TPBAddress": "1759 35 Ave E",
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "SKD",
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "Bol": "UB1234567890",
            "PO1": "Ref One",
            "PO2": "Ref Two",
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_time_critical(self):
        """
        Test build request - Time Critical
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "1200|LF3Q761752"

        abf_ship = ABFShip(ubbe_request=copied)
        ret = abf_ship._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "QuoteID": "LF3Q761752",
            "RequesterType": "3",
            "PayTerms": "P",
            "ProAutoAssign": "Y",
            "Instructions": "",
            "RequesterName": "BBE Expediting",
            "RequesterEmail": "customerservice@ubbe.com",
            "RequesterPhone": "8884206926",
            "RequesterPhoneExt": "1",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ShipName": "BBE Ottawa",
            "ShipContact": "BBE",
            "ShipNamePlus": "BBE",
            "ShipPhone": "7809326245",
            "ShipEmail": "customerservice@ubbe.com",
            "ShipAddress": "1540 Airport Road",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "ConsName": "BBE Ottawa",
            "ConsContact": "BBE",
            "ConsNamePlus": "BBE",
            "ConsPhone": "7809326245",
            "ConsEmail": "customerservice@ubbe.com",
            "ConsAddress": "140 THAD JOHNSON PRIV Suite 7",
            "TPBCity": "edmonton international airport",
            "TPBState": "AB",
            "TPBCountry": "CA",
            "TPBZip": "T9E0V6",
            "TPBName": "BBE Expediting",
            "TPBContact": "Customer Service",
            "TPBNamePlus": "Customer Service",
            "TPBPhone": "18884206926",
            "TPBEmail": "customerservice@ubbe.com",
            "TPBAddress": "1759 35 Ave E",
            "LWHType": "IN",
            "HN1": 1,
            "HT1": "SKD",
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "WT1": Decimal("100"),
            "CL1": 70,
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "InkJetPrinter": "Y",
            "FileFormat": "A",
            "LabelFormat": "Z",
            "LabelNum": "1",
            "TimeKeeper": "Y",
            "ShipDate": "08/12/2021",
        }
        self.assertDictEqual(expected, ret)

    def test_determine_service_name(self):
        """
        Test Determine Service Name.
        """
        ret = self._abf_ship._determine_service_name(service_code="LTL")
        expected = "LTL"
        self.assertEqual(expected, ret)

    def test_determine_service_name_spot(self):
        """
        Test Determine Service Name - Spot.
        """
        ret = self._abf_ship._determine_service_name(service_code="SV")
        expected = "Spot LTL"
        self.assertEqual(expected, ret)

    def test_determine_service_name_time_critical_12(self):
        """
        Test Determine Service Name - Time Critical 12:00.
        """
        ret = self._abf_ship._determine_service_name(service_code="1200")
        expected = "Guaranteed 1200"
        self.assertEqual(expected, ret)

    def test_determine_service_name_time_critical_17(self):
        """
        Test Determine Service Name - Time Critical 17:00.
        """
        ret = self._abf_ship._determine_service_name(service_code="1700")
        expected = "Guaranteed 1700"
        self.assertEqual(expected, ret)

    def test_ship_api_north_origin(self):
        """
        Test Ship - Inactive
        """
        copied = copy.deepcopy(self.request)
        copied["origin"]["province"] = "NT"
        abf_ship = ABFShip(ubbe_request=copied)

        with self.assertRaises(ShipException) as e:
            abf_ship.ship()

        self.assertEqual(
            e.exception.message,
            "ABF Ship (L275): No service available (North:YT,NT,NU).",
        )

    def test_ship_api_north_destination(self):
        """
        Test Ship - Inactive
        """
        copied = copy.deepcopy(self.request)
        copied["destination"]["province"] = "NU"
        abf_ship = ABFShip(ubbe_request=copied)

        with self.assertRaises(ShipException) as e:
            abf_ship.ship()

        self.assertEqual(
            e.exception.message,
            "ABF Ship (L275): No service available (North:YT,NT,NU).",
        )
