"""
    Title: Action Express Rate Unit Tests
    Description: Unit Tests for the Action Express Rate. Test Everything.
    Created: June 15, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.action_express.endpoints.ac_rate import ActionExpressRate
from api.exceptions.project import RequestError, RateException
from api.models import SubAccount, Carrier, CarrierAccount, Tax


class ACRateTests(TestCase):
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
        carrier = Carrier.objects.get(code=601)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
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
                    "package_type": "BOX",
                    "imperial_length": Decimal("4.17"),
                    "imperial_width": Decimal("4.17"),
                    "imperial_height": Decimal("4.17"),
                    "imperial_weight": Decimal("23.37"),
                },
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    601: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self.ac_rate = ActionExpressRate(ubbe_request=self.request)

    @staticmethod
    def mock_post_call(url, data):
        return Decimal("30.00")

    @staticmethod
    def mock_tax_call():
        return Tax.objects.first()

    @staticmethod
    def mock_none_call():
        return None

    @staticmethod
    def mock_error_call():
        raise RequestError()

    @staticmethod
    def mock_post_error_call(url, data):
        raise RequestError()

    @staticmethod
    def mock_key_error_call(customer, price_set):
        raise KeyError

    @staticmethod
    def mock_exception_call(cost):
        raise Exception

    @patch("api.apis.services.taxes.taxes.Taxes.get_tax", new=mock_none_call)
    def test_format_response_none_tax(self) -> None:
        """
        Test Package item for rate formatting.
        """
        responses = [
            {
                "request": {
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": Decimal("7.87"),
                            "Width": Decimal("7.87"),
                            "Height": Decimal("7.87"),
                            "Weight": Decimal("44.09"),
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1St Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1St Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-10T14:00:00+00:00",
                        "LatestTime": "2021-09-11T00:00:00+00:00",
                    },
                    "RequestedBy": "ubbe (BBE Expediting Ltd)",
                    "Description": "ubbe shipment: ",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Comments": "",
                    "Weight": Decimal("44.09"),
                    "Quantity": 1,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        }
                    ],
                },
                "cost": Decimal("10"),
                "service": "REG:Regular",
                "service_cost": Decimal("0.00"),
            }
        ]

        self.ac_rate._format_response(responses=responses)
        expected = [
            {
                "carrier_id": 601,
                "carrier_name": "Action Express",
                "service_code": "REG",
                "service_name": "Regular",
                "freight": Decimal("10.00"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.50"),
                "tax_percent": Decimal("5"),
                "total": Decimal("10.50"),
            }
        ]
        del self.ac_rate._response[0]["delivery_date"]
        del self.ac_rate._response[0]["transit_days"]
        self.assertEqual(expected, self.ac_rate._response)

    @patch("api.apis.services.taxes.taxes.Taxes.get_tax", new=mock_error_call)
    def test_format_response_request_error(self) -> None:
        """
        Test Package item for rate formatting.
        """
        responses = [
            {
                "request": {
                    "Customer": "bdd21daf-7078-4325-80df-0a95f90eb665",
                    "PriceSet": "a79c8ce0-f59d-4ed2-8fa9-0b114bd21970",
                    "CustomerContact": {
                        "Name": "Customer Service",
                        "Email": "customerservice@ubbe.ca",
                        "Phone": "8884206926",
                    },
                    "Items": [
                        {
                            "Description": "Package",
                            "Length": Decimal("7.87"),
                            "Width": Decimal("7.87"),
                            "Height": Decimal("7.87"),
                            "Weight": Decimal("44.09"),
                        }
                    ],
                    "CollectionLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1St Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton",
                        "State": "AB",
                        "PostalCode": "T5T4R7",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "DeliveryLocation": {
                        "ContactName": "",
                        "CompanyName": "BBE",
                        "AddressLine1": "705-1St Avenue",
                        "AddressLine2": "",
                        "City": "Edmonton International Airport",
                        "State": "AB",
                        "PostalCode": "T9E0V6",
                        "Country": "CA",
                        "Email": "",
                        "Phone": "",
                    },
                    "CollectionArrivalWindow": {
                        "EarliestTime": "2021-09-10T14:00:00+00:00",
                        "LatestTime": "2021-09-11T00:00:00+00:00",
                    },
                    "RequestedBy": "ubbe (BBE Expediting Ltd)",
                    "Description": "ubbe shipment: ",
                    "CollectionSignatureRequired": True,
                    "DeliverySignatureRequired": True,
                    "ReferenceNumber": "/",
                    "PurchaseOrderNumber": "",
                    "Comments": "",
                    "Weight": Decimal("44.09"),
                    "Quantity": 1,
                    "PriceModifiers": [
                        {
                            "ID": "827ac53b-3cae-40a2-a5ad-c714bb3884b3",
                            "Name": "BBE To & From Edmonton Area",
                        }
                    ],
                },
                "cost": Decimal("10"),
                "service": "REG:Regular",
                "service_cost": Decimal("0.00"),
            }
        ]

        self.ac_rate._format_response(responses=responses)
        expected = [
            {
                "carrier_id": 601,
                "carrier_name": "Action Express",
                "service_code": "REG",
                "service_name": "Regular",
                "freight": Decimal("10.00"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.50"),
                "tax_percent": Decimal("5"),
                "total": Decimal("10.50"),
            }
        ]
        del self.ac_rate._response[0]["delivery_date"]
        del self.ac_rate._response[0]["transit_days"]
        self.assertEqual(expected, self.ac_rate._response)

    @patch("api.apis.services.taxes.taxes.Taxes.get_tax", new=mock_tax_call)
    @patch(
        "api.apis.carriers.action_express.endpoints.ac_api.ActionExpressApi._post",
        new=mock_post_call,
    )
    def test_rate(self) -> None:
        """
        Test Package item for rate formatting.
        """
        response = self.ac_rate.rate()
        expected = [
            {
                "carrier_id": 601,
                "carrier_name": "Action Express",
                "service_code": "ACCourier",
                "service_name": "Courier",
                "freight": Decimal("28.57"),
                "surcharge": Decimal("0"),
                "tax": Decimal("1.43"),
                "tax_percent": Decimal("5.00"),
                "total": Decimal("30.00"),
                "transit_days": 1,
            }
        ]
        del self.ac_rate._response[0]["delivery_date"]
        self.assertEqual(expected, response)

    @patch("api.apis.services.taxes.taxes.Taxes.get_tax", new=mock_tax_call)
    @patch(
        "api.apis.carriers.action_express.endpoints.ac_api.ActionExpressApi._post",
        new=mock_post_call,
    )
    @patch(
        "api.apis.carriers.action_express.helpers.order.Order.create_order",
        new=mock_key_error_call,
    )
    def test_rate(self) -> None:
        """
        Test Package item for rate formatting.
        """

        with self.assertRaises(RateException) as context:
            response = self.ac_rate.rate()

        self.assertEqual("AE Rate (L90): ", context.exception.message)

    # @patch('api.apis.services.taxes.taxes.Taxes.get_tax', new=mock_tax_call)
    # @patch('api.apis.carriers.action_express.endpoints.ac_api.ActionExpressApi._post', new=mock_post_error_call)
    # def test_rate(self) -> None:
    #     """
    #         Test Package item for rate formatting.
    #     """
    #
    #     with self.assertRaises(RateException) as context:
    #         response = self.ac_rate.rate()
    #
    #     self.assertEqual("AE Rate (L100): Request Error, Data: {'Customer': 'ACTION EXPRESS', 'PriceSet': 'ACTION EXPRESS', 'CustomerContact': {'CustomerID': 'ACTION EXPRESS', 'Name': 'Customer Service', 'Email': 'customerservice@ubbe.ca', 'Phone': '8884206926'}, 'Items': [{'Description': 'Box', 'Length': Decimal('4.17'), 'Width': Decimal('4.17'), 'Height': Decimal('4.17'), 'Weight': Decimal('23.37')}, {'Description': 'My Awesome Package', 'Length': Decimal('4.17'), 'Width': Decimal('4.17'), 'Height': Decimal('4.17'), 'Weight': Decimal('23.37')}], 'CollectionLocation': {'ContactName': '', 'CompanyName': 'BBE Ottawa', 'AddressLine1': '1540 Airport Road', 'AddressLine2': '', 'City': 'Edmonton International Airport', 'State': 'AB', 'PostalCode': 'T9E 0V6', 'Country': 'CA', 'Email': '', 'Phone': ''}, 'DeliveryLocation': {'ContactName': '', 'CompanyName': 'BBE Ottawa', 'AddressLine1': '1540 Airport Road', 'AddressLine2': '', 'City': 'Edmonton', 'State': 'AB', 'PostalCode': 'T5T 4R7', 'Country': 'CA', 'Email': '', 'Phone': ''}, 'CollectionArrivalWindow': {}, 'RequestedBy': 'ubbe (BBE Expediting Ltd)', 'Description': 'ubbe shipment: ', 'CollectionSignatureRequired': True, 'DeliverySignatureRequired': True, 'ReferenceNumber': '/', 'PurchaseOrderNumber': '', 'Comments': '', 'Weight': Decimal('46.74'), 'Quantity': 2, 'PriceModifiers': [{'ID': '827ac53b-3cae-40a2-a5ad-c714bb3884b3', 'Name': 'BBE To & From Edmonton Area'}]}", context.exception.message)
