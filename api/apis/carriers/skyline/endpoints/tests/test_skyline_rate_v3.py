import copy
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.skyline.endpoints.skyline_rate_v3 import SkylineRate
from api.exceptions.project import RateException
from api.models import SubAccount
from api.utilities.carriers import CarrierUtility


class SkylineRateV3Tests(TestCase):
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
            "carrier_id": [708],
            "is_metric": True,
            "packages": [
                {
                    "quantity": 1,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal(".9"),
                    "nog_id": 88,
                },
                {
                    "quantity": 1,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "is_frozen": True,
                    "nog_id": 88,
                },
                {
                    "quantity": 1,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "is_cooler": True,
                    "nog_id": 88,
                },
            ],
            "is_delivery": True,
            "is_pickup": True,
            "is_food": False,
            "destination": {
                "address": "123 Ave",
                "city": "Edmonton",
                "company_name": "The Brain",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "YEG",
            },
            "origin": {
                "address": "123 Ave",
                "city": "Qikiqtarjuaq",
                "company_name": "The Brain",
                "country": "CA",
                "postal_code": "X0A0B0",
                "province": "NU",
                "has_shipping_bays": True,
                "base": "YVM",
            },
            "mid_d": {
                "address": "123 Ave",
                "city": "Edmonton",
                "company_name": "The Brain",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "YEG",
            },
            "mid_o": {
                "address": "123 Ave",
                "city": "Qikiqtarjuaq",
                "company_name": "The Brain",
                "country": "CA",
                "postal_code": "X0A0B0",
                "province": "NU",
                "has_shipping_bays": True,
                "base": "YVM",
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
            "carrier_id": [708],
            "is_metric": True,
            "packages": [
                {
                    "quantity": 1,
                    "description": "TEST",
                    "length": Decimal("10.00"),
                    "width": Decimal("10.00"),
                    "height": Decimal("10.00"),
                    "weight": Decimal("20.00"),
                    "nog_id": 88,
                }
            ],
            "is_delivery": False,
            "is_pickup": False,
            "is_food": False,
            "destination": {
                "address": "123 Ave",
                "city": "Edmonton",
                "company_name": "The Brain",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "YEG",
            },
            "origin": {
                "address": "123 Ave",
                "city": "Qikiqtarjuaq",
                "company_name": "The Brain",
                "country": "CA",
                "postal_code": "X0A0B0",
                "province": "NU",
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

        self.response = [
            {
                "status": "ok",
                "errors": None,
                "data": {
                    "Surcharges": [
                        {
                            "Name": "5T Nav Can Surcharge",
                            "Amount": 14.06,
                            "Percentage": 5.0,
                        },
                        {"Name": "ACS Screening Fee", "Amount": 7.5, "Percentage": 0.0},
                        {
                            "Name": "5T Fuel Surcharge",
                            "Amount": 73.13,
                            "Percentage": 26.0,
                        },
                        {
                            "Name": "DangerousGoodsCharge",
                            "Amount": 0.0,
                            "Percentage": None,
                        },
                        {"Name": "ValuationCharge", "Amount": 0.0, "Percentage": None},
                        {"Name": "FuelCharge", "Amount": 0.0, "Percentage": None},
                    ],
                    "PackagePrices": [
                        {
                            "RatePriorityId": 1,
                            "RatePriorityName": "General",
                            "BillableWeight": 1.0,
                            "DimensionalWeight": 0.0,
                            "Freight": 6.86,
                        },
                        {
                            "RatePriorityId": 1,
                            "RatePriorityName": "General",
                            "BillableWeight": 20.0,
                            "DimensionalWeight": 0.0,
                            "Freight": 137.2,
                        },
                        {
                            "RatePriorityId": 1,
                            "RatePriorityName": "General",
                            "BillableWeight": 20.0,
                            "DimensionalWeight": 0.0,
                            "Freight": 137.2,
                        },
                    ],
                    "Taxes": [{"Amount": 18.8, "Name": "GST", "Percentage": 0.05}],
                    "TotalPreTax": 375.95,
                    "Total": 394.75,
                },
            },
            {
                "status": "ok",
                "errors": None,
                "data": {
                    "Surcharges": [
                        {
                            "Name": "5T Nav Can Surcharge",
                            "Amount": 19.72,
                            "Percentage": 5.0,
                        },
                        {"Name": "ACS Screening Fee", "Amount": 7.5, "Percentage": 0.0},
                        {
                            "Name": "5T Fuel Surcharge",
                            "Amount": 102.55,
                            "Percentage": 26.0,
                        },
                        {
                            "Name": "DangerousGoodsCharge",
                            "Amount": 0.0,
                            "Percentage": None,
                        },
                        {"Name": "ValuationCharge", "Amount": 0.0, "Percentage": None},
                        {"Name": "FuelCharge", "Amount": 0.0, "Percentage": None},
                    ],
                    "PackagePrices": [
                        {
                            "RatePriorityId": 35,
                            "RatePriorityName": "Guaranteed",
                            "BillableWeight": 1.0,
                            "DimensionalWeight": 0.0,
                            "Freight": 9.62,
                        },
                        {
                            "RatePriorityId": 35,
                            "RatePriorityName": "Guaranteed",
                            "BillableWeight": 20.0,
                            "DimensionalWeight": 0.0,
                            "Freight": 192.4,
                        },
                        {
                            "RatePriorityId": 35,
                            "RatePriorityName": "Guaranteed",
                            "BillableWeight": 20.0,
                            "DimensionalWeight": 0.0,
                            "Freight": 192.4,
                        },
                    ],
                    "Taxes": [{"Amount": 26.21, "Name": "GST", "Percentage": 0.05}],
                    "TotalPreTax": 524.19,
                    "Total": 550.4,
                },
            },
        ]
        self.single_response = {
            "status": "ok",
            "errors": None,
            "data": {
                "Surcharges": [
                    {
                        "Name": "5T Nav Can Surcharge",
                        "Amount": 14.06,
                        "Percentage": 5.0,
                    },
                    {"Name": "ACS Screening Fee", "Amount": 7.5, "Percentage": 0.0},
                    {"Name": "5T Fuel Surcharge", "Amount": 73.13, "Percentage": 26.0},
                    {"Name": "DangerousGoodsCharge", "Amount": 0.0, "Percentage": None},
                    {"Name": "ValuationCharge", "Amount": 0.0, "Percentage": None},
                    {"Name": "FuelCharge", "Amount": 0.0, "Percentage": None},
                ],
                "PackagePrices": [
                    {
                        "RatePriorityId": 1,
                        "RatePriorityName": "General",
                        "BillableWeight": 1.0,
                        "DimensionalWeight": 0.0,
                        "Freight": 6.86,
                    },
                    {
                        "RatePriorityId": 1,
                        "RatePriorityName": "General",
                        "BillableWeight": 20.0,
                        "DimensionalWeight": 0.0,
                        "Freight": 137.2,
                    },
                    {
                        "RatePriorityId": 1,
                        "RatePriorityName": "General",
                        "BillableWeight": 20.0,
                        "DimensionalWeight": 0.0,
                        "Freight": 137.2,
                    },
                ],
                "Taxes": [{"Amount": 18.8, "Name": "GST", "Percentage": 0.05}],
                "TotalPreTax": 375.95,
                "Total": 394.75,
            },
        }
        self.api = SkylineRate(gobox_request=self.gobox_request)

    def test_skyline_rate_init(self):
        api = SkylineRate(gobox_request=self.gobox_request)

        self.assertIsInstance(api, SkylineRate)

    def test_build(self):
        self.api._rate_priorities()
        self.api._process_packages()
        self.api._build()

        expected = [
            {
                "DestinationAirportCode": "YEG",
                "OriginAirportCode": "YVM",
                "TotalPackages": 3,
                "TotalWeight": Decimal("41.00"),
                "CustomerId": "128",
                "Packages": [
                    {
                        "Quantity": Decimal("1"),
                        "Description": "TEST",
                        "Height": Decimal("10.00"),
                        "Length": Decimal("10.00"),
                        "Width": Decimal("10.00"),
                        "Weight": "1.00",
                        "IsDangerousGood": False,
                        "IsCooler": False,
                        "IsFrozen": False,
                        "IsENV": True,
                        "NogId": 88,
                        "RatePriorityId": "1",
                        "NatureOfGoodsId": 88,
                    },
                    {
                        "Quantity": Decimal("1"),
                        "Description": "TEST",
                        "Height": Decimal("10.00"),
                        "Length": Decimal("10.00"),
                        "Width": Decimal("10.00"),
                        "Weight": "20.00",
                        "IsDangerousGood": False,
                        "IsCooler": False,
                        "IsFrozen": True,
                        "IsENV": False,
                        "NogId": 88,
                        "RatePriorityId": "1",
                        "NatureOfGoodsId": 88,
                    },
                    {
                        "Quantity": Decimal("1"),
                        "Description": "TEST",
                        "Height": Decimal("10.00"),
                        "Length": Decimal("10.00"),
                        "Width": Decimal("10.00"),
                        "Weight": "20.00",
                        "IsDangerousGood": False,
                        "IsCooler": True,
                        "IsFrozen": False,
                        "IsENV": False,
                        "NogId": 88,
                        "RatePriorityId": "1",
                        "NatureOfGoodsId": 88,
                    },
                ],
                "API_Key": "e6ebb74d5ade45c68814c066f1175670",
            },
            {
                "DestinationAirportCode": "YEG",
                "OriginAirportCode": "YVM",
                "TotalPackages": 3,
                "TotalWeight": Decimal("41.00"),
                "CustomerId": "128",
                "Packages": [
                    {
                        "Quantity": Decimal("1"),
                        "Description": "TEST",
                        "Height": Decimal("10.00"),
                        "Length": Decimal("10.00"),
                        "Width": Decimal("10.00"),
                        "Weight": "1.00",
                        "IsDangerousGood": False,
                        "IsCooler": False,
                        "IsFrozen": False,
                        "IsENV": True,
                        "NogId": 88,
                        "RatePriorityId": "2",
                        "NatureOfGoodsId": 88,
                    },
                    {
                        "Quantity": Decimal("1"),
                        "Description": "TEST",
                        "Height": Decimal("10.00"),
                        "Length": Decimal("10.00"),
                        "Width": Decimal("10.00"),
                        "Weight": "20.00",
                        "IsDangerousGood": False,
                        "IsCooler": False,
                        "IsFrozen": True,
                        "IsENV": False,
                        "NogId": 88,
                        "RatePriorityId": "2",
                        "NatureOfGoodsId": 88,
                    },
                    {
                        "Quantity": Decimal("1"),
                        "Description": "TEST",
                        "Height": Decimal("10.00"),
                        "Length": Decimal("10.00"),
                        "Width": Decimal("10.00"),
                        "Weight": "20.00",
                        "IsDangerousGood": False,
                        "IsCooler": True,
                        "IsFrozen": False,
                        "IsENV": False,
                        "NogId": 88,
                        "RatePriorityId": "2",
                        "NatureOfGoodsId": 88,
                    },
                ],
                "API_Key": "e6ebb74d5ade45c68814c066f1175670",
            },
        ]
        self.assertListEqual(self.api._skyline_requests, expected)

    def test_build_bad(self):
        api = SkylineRate(gobox_request=self.gobox_request_bad)

        with self.assertRaises(RateException):
            api._rate_priorities()
            api._process_packages()
            api._build()

    def test_format_response(self):
        self.api._response = self.response
        self.api._format_response()

        expected = [
            {
                "carrier_id": 708,
                "carrier_name": "Canadian North",
                "service_code": "1",
                "service_name": "General",
                "freight": Decimal("281.26"),
                "surcharge": Decimal("94.69"),
                "tax": Decimal("18.80"),
                "tax_percent": 5.0,
                "total": Decimal("394.75"),
                "transit_days": -1,
                "delivery_date": "0001-01-01T00:00:00",
                "mid_o": {
                    "address": "123 Ave",
                    "city": "Qikiqtarjuaq",
                    "company_name": "The Brain",
                    "country": "CA",
                    "postal_code": "X0A0B0",
                    "province": "NU",
                    "has_shipping_bays": True,
                    "base": "YVM",
                },
                "mid_d": {
                    "address": "123 Ave",
                    "city": "Edmonton",
                    "company_name": "The Brain",
                    "country": "CA",
                    "postal_code": "T9E0V6",
                    "province": "AB",
                    "has_shipping_bays": True,
                    "base": "YEG",
                },
            },
            {
                "carrier_id": 708,
                "carrier_name": "Canadian North",
                "service_code": "35",
                "service_name": "Guaranteed",
                "freight": Decimal("394.42"),
                "surcharge": Decimal("129.77"),
                "tax": Decimal("26.21"),
                "tax_percent": 5.0,
                "total": Decimal("550.4"),
                "transit_days": -1,
                "delivery_date": "0001-01-01T00:00:00",
                "mid_o": {
                    "address": "123 Ave",
                    "city": "Qikiqtarjuaq",
                    "company_name": "The Brain",
                    "country": "CA",
                    "postal_code": "X0A0B0",
                    "province": "NU",
                    "has_shipping_bays": True,
                    "base": "YVM",
                },
                "mid_d": {
                    "address": "123 Ave",
                    "city": "Edmonton",
                    "company_name": "The Brain",
                    "country": "CA",
                    "postal_code": "T9E0V6",
                    "province": "AB",
                    "has_shipping_bays": True,
                    "base": "YEG",
                },
            },
        ]
        self.assertListEqual(self.api._response, expected)

    def test_parse_prices_bad_key(self):
        response = copy.deepcopy(self.single_response)

        del response["data"]["PackagePrices"]

        with self.assertRaises(RateException):
            self.api._parse_prices(response=response)

    def test_parse_prices_bad_two_error(self):
        response = copy.deepcopy(self.single_response)

        response["data"]["Taxes"][0]["Amount"] = None

        with self.assertRaises(RateException):
            self.api._parse_prices(response=response)

    def test_parse_prices_bad_conversion_fail(self):
        response = copy.deepcopy(self.single_response)

        response["data"]["Total"] = {}

        with self.assertRaises(RateException):
            self.api._parse_prices(response=response)

    def test_get_total_of_key_bad_key(self):
        test = [
            {"name": "5T Nav Can Surcharge", "amount": 14.06, "percentage": 5.0},
            {"name": "ACS Screening Fee", "amount": 7.5, "percentage": 0.0},
            {"name": "5T Fuel Surcharge", "amount": 73.13, "percentage": 26.0},
            {"name": "DangerousGoodsCharge", "amount": 0.0, "percentage": None},
            {"name": "ValuationCharge", "amount": 0.0, "percentage": None},
            {"name": "FuelCharge", "amount": 0.0, "percentage": None},
        ]

        with self.assertRaises(RateException):
            self.api._get_total_of_key(items=test, key="Namee")

    def test_get_total_of_key_bad_instance(self):
        test = {}

        with self.assertRaises(RateException):
            self.api._get_total_of_key(items=test, key="Namee")

    def test_add_pickup_delivery(self):
        data = self.api._add_pickup_delivery()
        expected = {
            "total": Decimal("18.90"),
            "freight": Decimal("18.00"),
            "taxes": Decimal("0.90"),
            "service_name": "Local Pickup Charge",
        }
        self.assertDictEqual(data, expected)

    def test_get_pickup_or_delivery_cost_bad(self):
        api = SkylineRate(gobox_request=self.gobox_request_bad)
        data = api._get_pickup_or_delivery_cost()

        self.assertListEqual(data, [])

    def test_add_pickup_delivery_bad(self):
        with self.assertRaises(RateException):
            api = SkylineRate(gobox_request=self.gobox_request_bad)
            data = api._add_pickup_delivery()

    def test_get_pickup_or_delivery_cost(self):
        data = self.api._get_pickup_or_delivery_cost()
        expected = [
            {
                "carrier_id": 708,
                "carrier_name": "Canadian North",
                "service_code": "PICK_DEL",
                "service_name": "Local Pickup Charge",
                "freight": Decimal("18.00"),
                "surcharge": Decimal("0.00"),
                "tax_percent": Decimal("4.76"),
                "tax": Decimal("0.90"),
                "total": Decimal("18.90"),
                "transit_days": 1,
            }
        ]
        del data[0]["delivery_date"]
        self.assertListEqual(data, expected)

    def test_add_pickup_delivery_no_charge(self):
        self.api._is_pickup = False
        self.api._is_delivery = False

        with self.assertRaises(RateException):
            data = self.api._add_pickup_delivery()

    def test_add_pickup_delivery_good_d(self):
        self.api._is_pickup = False
        self.api._gobox_request["destination"]["city"] = "Inuvik"
        data = self.api._add_pickup_delivery()
        expected = {
            "total": Decimal("18.90"),
            "freight": Decimal("18.00"),
            "taxes": Decimal("0.90"),
            "service_name": "Local Delivery Charge",
        }
        self.assertDictEqual(data, expected)
