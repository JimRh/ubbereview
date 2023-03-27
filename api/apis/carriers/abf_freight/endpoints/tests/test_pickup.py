"""
    Title: ABF Pickup Unit Tests
    Description: Unit Tests for the ABF Pickup. Test Everything.
    Created: June 28, 2022
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

from api.apis.carriers.abf_freight.endpoints.abf_pickup import ABFPickup
from api.exceptions.project import PickupException
from api.globals.carriers import ABF_FREIGHT
from api.models import SubAccount, Carrier, CarrierAccount, API


class ABFPickupTests(TestCase):
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
            "tracking_number": "KCTESTTRACK",
        }

        self.response = xmltodict.parse(
            xml_input='<?xml version="1.0"?><ABF><CONFIRMATION>WWW0000000</CONFIRMATION><NUMERRORS>0</NUMERRORS></ABF>'
        )
        self.response_error = xmltodict.parse(
            xml_input='<?xml version="1.0"?><ABF><NUMERRORS>1</NUMERRORS><ERROR><ERRORCODE>45</ERRORCODE><ERRORMESSAGE>PICKUP DATE can not be in the past.</ERRORMESSAGE></ERROR></ABF>'
        )

        self._abf_pickup = ABFPickup(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test build address origin.
        """
        ret = self._abf_pickup._build_address(
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
        ret = self._abf_pickup._build_address(
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

    def test_build_packages(self):
        """
        Test build packages.
        """
        ret = self._abf_pickup._build_packages()
        expected = {
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "WT1": Decimal("100.00"),
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
        abf_pickup = ABFPickup(ubbe_request=copied)

        ret = abf_pickup._build_packages()
        expected = {
            "Desc1": "Test",
            "PN1": 1,
            "PT1": "SKD",
            "WT1": Decimal("100.00"),
            "CL1": 70,
            "Desc2": "Test",
            "PN2": 1,
            "PT2": "SKD",
            "WT2": Decimal("100.00"),
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

        abf_pickup = ABFPickup(ubbe_request=copied)
        ret = abf_pickup._build_packages()
        expected = {
            "Desc1": "TEST",
            "PN1": 1,
            "PT1": "DR",
            "WT1": Decimal("100.00"),
            "CL1": 70,
            "HZ1": "Y",
        }
        self.assertDictEqual(expected, ret)

    def test_build_pickup(self):
        """
        Test build pickup.
        """
        ret = self._abf_pickup._build_pickup()
        expected = {
            "PickupDate": "08/12/2021",
            "AT": "10:00",
            "OT": "10:00",
            "CT": "16:00",
        }
        self.assertDictEqual(expected, ret)

    def test_build_pickup_no_pickup(self):
        """
        Test build pickup - no pickup.
        """
        copied = copy.deepcopy(self.request)
        del copied["pickup"]
        pickup_date = datetime.datetime.today().date()

        abf_pickup = ABFPickup(ubbe_request=copied)
        ret = abf_pickup._build_pickup()
        expected = {
            "PickupDate": pickup_date.strftime("%m/%d/%Y"),
            "AT": "09:00",
            "OT": "09:00",
            "CT": "18:00",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request(self):
        """
        Test build request.
        """
        ret = self._abf_pickup._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "RequesterType": "3",
            "PayTerms": "P",
            "Pronumber": "KCTESTTRACK",
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
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "PickupDate": "08/12/2021",
            "AT": "10:00",
            "OT": "10:00",
            "CT": "16:00",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_dg(self):
        """
        Test build request.
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

        abf_pickup = ABFPickup(ubbe_request=copied)
        ret = abf_pickup._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "RequesterType": "3",
            "PayTerms": "P",
            "Pronumber": "KCTESTTRACK",
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
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "PickupDate": "08/12/2021",
            "AT": "10:00",
            "OT": "10:00",
            "CT": "16:00",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_time_critical(self):
        """
        Test build request.
        """
        copied = copy.deepcopy(self.request)
        copied["service_code"] = "1200|LF3Q761752"

        abf_pickup = ABFPickup(ubbe_request=copied)
        ret = abf_pickup._build_request()
        expected = {
            "ID": "BBEYZF",
            "Test": "Y",
            "RequesterType": "3",
            "PayTerms": "P",
            "Pronumber": "KCTESTTRACK",
            "Instructions": "",
            "TimeKeeper": "Y",
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
            "Bol": "UB1234567890",
            "PO1": "",
            "PO2": "",
            "PickupDate": "08/12/2021",
            "AT": "10:00",
            "OT": "10:00",
            "CT": "16:00",
        }
        self.assertDictEqual(expected, ret)

    def test_format_response(self):
        """
        Test Format Response for ABF
        """
        ret = self._abf_pickup._format_response(response=self.response)
        expected = {
            "pickup_id": "WWW0000000",
            "pickup_message": "Success",
            "pickup_status": "Booked",
        }
        self.assertDictEqual(expected, ret)

    def test_format_response_empty(self):
        """
        Test Format Response for ABF
        """
        ret = self._abf_pickup._format_response(response={})
        expected = {
            "pickup_id": "",
            "pickup_message": "(ABF) Pickup Request Failed.",
            "pickup_status": "Failed",
        }
        self.assertDictEqual(expected, ret)

    def test_format_response_error(self):
        """
        Test Format Response for ABF
        """
        ret = self._abf_pickup._format_response(response=self.response_error)
        expected = {
            "pickup_id": "",
            "pickup_message": "PICKUP DATE can not be in the past.(45).",
            "pickup_status": "Failed",
        }
        self.assertDictEqual(expected, ret)
