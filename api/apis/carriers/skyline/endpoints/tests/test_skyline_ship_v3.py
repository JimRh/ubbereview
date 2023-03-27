from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.skyline.endpoints.skyline_ship_v3 import SkylineShip
from api.exceptions.project import ShipException
from api.models import SubAccount
from api.utilities.carriers import CarrierUtility


class SkylineShipV3Tests(TestCase):
    fixtures = [
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
        self.user = User.objects.get(pk=3)
        self.subaccount = SubAccount.objects.first()

        carrier_accounts = CarrierUtility().get_carrier_accounts(
            sub_account=self.subaccount, carrier_list=[708]
        )

        self.gobox_request = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "pickup": {
                "start_time": "08:00",
                "date": "2019-02-14",
                "end_time": "16:30",
            },
            "origin": {
                "address": "1759 35 Avenue E",
                "city": "Edmonton",
                "province": "AB",
                "country": "CA",
                "postal_code": "T9E0V6",
                "base": "YEG",
                "email": "developer@bbex.com",
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "phone": "7809326245",
            },
            "destination": {
                "address": "2158 Airport Road",
                "city": "Inuvik",
                "province": "NT",
                "country": "CA",
                "postal_code": "X0E0T0",
                "base": "YEV",
                "email": "developer@bbex.com",
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "phone": "7809326245",
            },
            "packages": [
                {
                    "quantity": 3,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "package_type": "BOX",
                    "is_frozen": False,
                    "is_cooler": True,
                    "nog_id": 88,
                },
                {
                    "quantity": 8,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "package_type": "BOX",
                    "is_frozen": True,
                    "is_cooler": False,
                    "nog_id": 88,
                },
                {
                    "quantity": 4,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "package_type": "BOX",
                    "is_frozen": False,
                    "is_cooler": False,
                    "nog_id": 88,
                },
            ],
            "reference_one": "SOMEREF",
            "is_food": False,
            "is_metric": True,
            "api_client_email": "",
            "other_legs": {},
            "carrier_id": 708,
            "service_code": "1",
            "ultimate_origin": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "Some Road",
                "city": "Edmonton",
                "country": "CA",
                "province": "AB",
                "postal_code": "T5T4R7",
                "has_shipping_bays": True,
            },
            "ultimate_destination": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "Some Road",
                "city": "Inuvik",
                "country": "CA",
                "province": "NT",
                "postal_code": "X0E0T0",
                "has_shipping_bays": True,
            },
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": self.user,
                "carrier_accounts": carrier_accounts,
                "air_list": CarrierUtility().get_air(),
                "ltl_list": CarrierUtility().get_ltl(),
                "ftl_list": CarrierUtility().get_ftl(),
                "courier_list": CarrierUtility().get_courier(),
                "sealift_list": CarrierUtility().get_sealift(),
            },
        }

        self.gobox_request_bad = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "pickup": {
                "start_time": "08:00",
                "date": "2019-02-14",
                "end_time": "16:30",
            },
            "origin": {
                "address": "1759 35 Avenue E",
                "city": "Edmonton",
                "province": "AB",
                "country": "CA",
                "postal_code": "T9E0V6",
                "email": "developer@bbex.com",
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "phone": "7809326245",
            },
            "destination": {
                "address": "2158 Airport Road",
                "city": "Inuvik",
                "province": "NT",
                "country": "CA",
                "postal_code": "X0E0T0",
                "base": "YEV",
                "email": "developer@bbex.com",
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "phone": "7809326245",
            },
            "packages": [
                {
                    "quantity": 3,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "package_type": "BOX",
                    "is_frozen": False,
                    "is_cooler": False,
                    "nog_id": 88,
                },
                {
                    "quantity": 8,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "package_type": "BOX",
                    "is_frozen": False,
                    "is_cooler": False,
                    "nog_id": 88,
                },
                {
                    "quantity": 4,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "package_type": "BOX",
                    "is_frozen": False,
                    "is_cooler": False,
                    "nog_id": 88,
                },
            ],
            "reference_one": "SOMEREF",
            "is_food": False,
            "is_metric": True,
            "api_client_email": "",
            "other_legs": {},
            "carrier_id": 708,
            "service_code": "1",
            "ultimate_origin": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "Some Road",
                "city": "Edmonton",
                "country": "CA",
                "province": "AB",
                "postal_code": "T5T4R7",
                "has_shipping_bays": True,
            },
            "ultimate_destination": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "Some Road",
                "city": "Inuvik",
                "country": "CA",
                "province": "NT",
                "postal_code": "X0E0T0",
                "has_shipping_bays": True,
            },
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": self.user,
                "carrier_accounts": carrier_accounts,
                "air_list": CarrierUtility().get_air(),
                "ltl_list": CarrierUtility().get_ltl(),
                "ftl_list": CarrierUtility().get_ftl(),
                "courier_list": CarrierUtility().get_courier(),
                "sealift_list": CarrierUtility().get_sealift(),
            },
        }

        self.response = {
            "status": "ok",
            "errors": None,
            "data": {
                "AirWaybillNumber": "518-YEG-10464963",
                "Charge": {
                    "BilledWeight": 300.0,
                    "DimensionalWeight": 0.0,
                    "WeightUnits": "kg",
                    "Freight": 1107.0,
                    "Surcharges": [
                        {
                            "Name": "5T Nav Can Surcharge",
                            "Amount": 55.35,
                            "Percentage": 5.0,
                        },
                        {
                            "Name": "ACS Screening Fee",
                            "Amount": 45.0,
                            "Percentage": 0.0,
                        },
                        {
                            "Name": "5T Fuel Surcharge",
                            "Amount": 287.82,
                            "Percentage": 26.0,
                        },
                    ],
                    "Taxes": [{"Name": "GST/HST", "Amount": 74.76, "Percentage": 5.0}],
                    "TotalTaxes": 74.76,
                    "Total": 1569.93,
                },
            },
        }
        self.api = SkylineShip(
            gobox_request=self.gobox_request, order_number="GO1234567890"
        )

    def test_skyline_rate_init(self):
        api = SkylineShip(gobox_request=self.gobox_request, order_number="GO1234567890")
        self.assertIsInstance(api, SkylineShip)

    def test_build(self):
        self.api._rate_priorities()
        self.api._process_packages()
        self.api._build()
        expected = {
            "Sender": {
                "Name": "TESTING INC",
                "Country": "CA",
                "City": "Edmonton",
                "PostalCode": "T5T4R7",
                "EmailAddress": "customerservice@ubbe.com",
                "Address": "Some Road",
                "Province": "AB",
                "Telephone": "7809326245",
                "Attention": "TESTING INC TWO",
            },
            "Recipient": {
                "Name": "TESTING INC",
                "Country": "CA",
                "City": "Inuvik",
                "PostalCode": "X0E0T0",
                "EmailAddress": "customerservice@ubbe.com",
                "Address": "Some Road",
                "Province": "NT",
                "Telephone": "7809326245",
                "Attention": "TESTING INC TWO",
            },
            "Packages": [
                {
                    "Quantity": Decimal("3"),
                    "Description": "TEST",
                    "Height": Decimal("30.00"),
                    "Length": Decimal("10.00"),
                    "Width": Decimal("10.00"),
                    "Weight": "60.00",
                    "IsDangerousGood": False,
                    "IsCooler": True,
                    "IsFrozen": False,
                    "IsENV": False,
                    "NogId": 88,
                    "RatePriorityId": "1",
                    "NatureOfGoodsId": 88,
                },
                {
                    "Quantity": Decimal("8"),
                    "Description": "TEST",
                    "Height": Decimal("80.00"),
                    "Length": Decimal("10.00"),
                    "Width": Decimal("10.00"),
                    "Weight": "160.00",
                    "IsDangerousGood": False,
                    "IsCooler": False,
                    "IsFrozen": True,
                    "IsENV": False,
                    "NogId": 88,
                    "RatePriorityId": "1",
                    "NatureOfGoodsId": 88,
                },
                {
                    "Quantity": Decimal("4"),
                    "Description": "TEST",
                    "Height": Decimal("40.00"),
                    "Length": Decimal("10.00"),
                    "Width": Decimal("10.00"),
                    "Weight": "80.00",
                    "IsDangerousGood": False,
                    "IsCooler": False,
                    "IsFrozen": False,
                    "IsENV": False,
                    "NogId": 88,
                    "RatePriorityId": "1",
                    "NatureOfGoodsId": 88,
                },
            ],
            "OtherCharges": [],
            "HandlingNotes": "",
            "SpecialInstructions": "",
            "OriginAirportCode": "YEG",
            "DestinationAirportCode": "YEV",
            "PurchaseOrder": "GO1234567890/SOMEREF",
            "DescriptionOfContents": "GoBox Shipment",
            "TotalPackages": 15,
            "TotalWeight": Decimal("300.00"),
            "API_Key": "e6ebb74d5ade45c68814c066f1175670",
            "CustomerId": "128",
        }
        self.assertDictEqual(self.api._skyline_request, expected)

    def test_build_bad(self):
        api = SkylineShip(
            gobox_request=self.gobox_request_bad, order_number="GO1234567890"
        )

        with self.assertRaises(ShipException):
            api._rate_priorities()
            api._process_packages()
            api._build()

    def test_format_response(self):
        self.api._rate_priorities()
        self.api._process_packages()
        self.api._skyline_response = self.response["data"]
        self.api._gobox_request["rp"] = "GEN"
        self.api._gobox_request["rp_id"] = 1
        self.api._format_response()

        expected = {
            "total": Decimal("1569.93"),
            "freight": Decimal("1107.00"),
            "taxes": Decimal("74.76"),
            "tax_percent": Decimal("4.76"),
            "surcharges": [
                {
                    "name": "5T Nav Can Surcharge",
                    "cost": Decimal("55.35"),
                    "percentage": Decimal("5.0"),
                },
                {
                    "name": "ACS Screening Fee",
                    "cost": Decimal("45.0"),
                    "percentage": Decimal("0.0"),
                },
                {
                    "name": "5T Fuel Surcharge",
                    "cost": Decimal("287.82"),
                    "percentage": Decimal("26.0"),
                },
            ],
            "surcharges_cost": Decimal("388.17"),
            "carrier_id": 708,
            "service_code": "1",
            "carrier_name": "Canadian North",
            "service_name": "GEN",
            "transit_days": -1,
            "delivery_date": "0001-01-01T00:00:00",
            "tracking_number": "518-YEG-10464963",
            "rp": "GEN",
        }
        self.assertDictEqual(self.api._response, expected)

    def test_do_not_ship(self):
        data = self.api._do_not_ship()
        expected = {
            "documents": [],
            "carrier_id": 708,
            "carrier_name": "Canadian North",
            "tracking_number": "",
            "total": Decimal("0.00"),
            "freight": Decimal("0.00"),
            "carrier_pickup_id": "",
            "api_pickup_id": "",
            "service_code": "1",
            "service_name": "",
            "surcharges": [],
            "surcharges_cost": Decimal("0.00"),
            "taxes": Decimal("0.00"),
            "tax_percent": Decimal("0.00"),
            "transit_days": 1,
        }
        del data["delivery_date"]
        self.assertDictEqual(data, expected)
