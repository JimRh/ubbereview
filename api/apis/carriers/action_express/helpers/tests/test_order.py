"""
    Title: Action Express Order Unit Tests
    Description: Unit Tests for the Action Express Order. Test Everything.
    Created: June 15, 2021
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""

import datetime
from decimal import Decimal

import pytz
from django.test import TestCase

from api.apis.carriers.action_express.helpers.order import Order


class ACOrderTests(TestCase):
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
        tz = pytz.timezone("America/Edmonton")
        self.date = datetime.datetime.now(tz)

        self.request_rate = {
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
            "total_quantity": Decimal("2"),
            "total_weight_imperial": Decimal("45.74"),
            "total_volume_imperial": Decimal("46.74"),
        }

        self.request_ship = {
            "pickup": {
                "start_time": "08:00",
                "date": "2021-09-08",
                "end_time": "16:30",
            },
            "origin": {
                "company_name": "BBE Ottawa",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 Thad Johnson Road",
                "city": "TEST",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
            },
            "packages": [
                {
                    "width": Decimal("10.6"),
                    "package_type": "BOX",
                    "quantity": 1,
                    "length": Decimal("10.6"),
                    "package": 1,
                    "description": "TEST",
                    "height": Decimal("10.6"),
                    "weight": Decimal("10.6"),
                    "imperial_length": Decimal("4.17"),
                    "imperial_width": Decimal("4.17"),
                    "imperial_height": Decimal("4.17"),
                    "imperial_weight": Decimal("23.37"),
                    "is_dangerous_good": False,
                    "volume": Decimal("0.00119102"),
                    "is_last": True,
                }
            ],
            "reference_one": "SOMEREF",
            "reference_two": "SOMEREF",
            "order_number": "ub0334041338M",
            "total_quantity": Decimal("2"),
            "total_weight_imperial": Decimal("45.74"),
            "total_volume_imperial": Decimal("46.74"),
        }

        self.order_rate = Order(ubbe_request=self.request_rate)
        self.order_ship = Order(ubbe_request=self.request_ship)

    def test_rate_create_item(self) -> None:
        """
        Test Package item for rate formatting.
        """

        ret = self.order_rate._create_item(package=self.request_rate["packages"][0])
        expected = {
            "Description": "Box",
            "Length": Decimal("4.17"),
            "Width": Decimal("4.17"),
            "Height": Decimal("4.17"),
            "Weight": Decimal("23.37"),
        }
        self.assertDictEqual(expected, ret)

    def test_rate_create_item_two(self) -> None:
        """
        Test Package item for rate formatting.
        """

        ret = self.order_rate._create_item(package=self.request_rate["packages"][1])
        expected = {
            "Description": "My Awesome Package",
            "Length": Decimal("4.17"),
            "Width": Decimal("4.17"),
            "Height": Decimal("4.17"),
            "Weight": Decimal("23.37"),
        }
        self.assertDictEqual(expected, ret)

    def test_rate_create_address_origin(self) -> None:
        """
        Test create address for rate formatting.
        """

        ret = self.order_rate._create_address(key="origin")
        expected = {
            "ContactName": "",
            "CompanyName": "BBE Ottawa",
            "AddressLine1": "1540 Airport Road",
            "AddressLine2": "",
            "City": "Edmonton International Airport",
            "State": "AB",
            "PostalCode": "T9E 0V6",
            "Country": "CA",
            "Email": "customerservice@ubbe.com",
            "Phone": "",
        }
        self.assertDictEqual(expected, ret)

    def test_rate_create_address_destination(self) -> None:
        """
        Test create address for rate formatting.
        """

        ret = self.order_rate._create_address(key="destination")
        expected = {
            "ContactName": "",
            "CompanyName": "BBE Ottawa",
            "AddressLine1": "1540 Airport Road",
            "AddressLine2": "",
            "City": "Edmonton",
            "State": "AB",
            "PostalCode": "T5T 4R7",
            "Country": "CA",
            "Email": "customerservice@ubbe.com",
            "Phone": "",
        }
        self.assertDictEqual(expected, ret)

    def test_rate_create_pickup(self) -> None:
        """
        Test create pickup for rate formatting.
        """

        ret = self.order_rate._create_pickup()
        expected = {}
        self.assertDictEqual(expected, ret)

    def test_rate_create_items(self) -> None:
        """
        Test create Package items for rate formatting.
        """
        description = ""
        description, packages = self.order_rate._create_items(description=description)
        expected = [
            {
                "Description": "Box",
                "Length": Decimal("4.17"),
                "Width": Decimal("4.17"),
                "Height": Decimal("4.17"),
                "Weight": Decimal("23.37"),
            },
            {
                "Description": "My Awesome Package",
                "Length": Decimal("4.17"),
                "Width": Decimal("4.17"),
                "Height": Decimal("4.17"),
                "Weight": Decimal("23.37"),
            },
        ]

        self.assertListEqual(expected, packages)
        self.assertEqual(
            "\nBox\n1 - 4.17x4.17x4.17 @ 23.37\nMy Awesome Package\n1 - 4.17x4.17x4.17 @ 23.37",
            description,
        )

    def test_rate_create_order(self) -> None:
        """
        Test Create Order for rate formatting.
        """

        ret = self.order_rate.create_order(customer="TEST1", price_set="TEST2")
        expected = {
            "Customer": "TEST1",
            "PriceSet": "TEST2",
            "CustomerContact": {
                "CustomerID": "TEST1",
                "Name": "Customer Service",
                "Email": "customerservice@ubbe.ca",
                "Phone": "8884206926",
            },
            "Items": [
                {
                    "Description": "Box",
                    "Length": Decimal("4.17"),
                    "Width": Decimal("4.17"),
                    "Height": Decimal("4.17"),
                    "Weight": Decimal("23.37"),
                },
                {
                    "Description": "My Awesome Package",
                    "Length": Decimal("4.17"),
                    "Width": Decimal("4.17"),
                    "Height": Decimal("4.17"),
                    "Weight": Decimal("23.37"),
                },
            ],
            "CollectionLocation": {
                "ContactName": "",
                "CompanyName": "BBE Ottawa",
                "AddressLine1": "1540 Airport Road",
                "AddressLine2": "",
                "City": "Edmonton International Airport",
                "State": "AB",
                "PostalCode": "T9E 0V6",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "Phone": "",
            },
            "DeliveryLocation": {
                "ContactName": "",
                "CompanyName": "BBE Ottawa",
                "AddressLine1": "1540 Airport Road",
                "AddressLine2": "",
                "City": "Edmonton",
                "State": "AB",
                "PostalCode": "T5T 4R7",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "Phone": "",
            },
            "CollectionArrivalWindow": {},
            "RequestedBy": "ubbe (BBE Expediting Ltd)",
            "Description": "\n/: \nBox\n1 - 4.17x4.17x4.17 @ 23.37\nMy Awesome Package\n1 - 4.17x4.17x4.17 @ 23.37",
            "CollectionSignatureRequired": True,
            "DeliverySignatureRequired": True,
            "ReferenceNumber": "/",
            "PurchaseOrderNumber": "",
            "Comments": "",
            "Weight": Decimal("468"),
            "Quantity": Decimal("2"),
            "PriceModifiers": [],
        }
        self.assertDictEqual(expected, ret)

    def test_ship_create_item(self) -> None:
        """
        Test Package item for rate formatting.
        """

        ret = self.order_ship._create_item(package=self.request_rate["packages"][0])
        expected = {
            "Description": "Box",
            "Length": Decimal("4.17"),
            "Width": Decimal("4.17"),
            "Height": Decimal("4.17"),
            "Weight": Decimal("23.37"),
        }
        self.assertDictEqual(expected, ret)

    def test_ship_create_address_origin(self) -> None:
        """
        Test create address for rate formatting.
        """

        ret = self.order_ship._create_address(key="origin")
        expected = {
            "ContactName": "TESTING INC TWO",
            "CompanyName": "BBE Ottawa",
            "AddressLine1": "1540 Airport Road",
            "AddressLine2": "",
            "City": "Edmonton International Airport",
            "State": "AB",
            "PostalCode": "T9E 0V6",
            "Country": "CA",
            "Email": "customerservice@ubbe.com",
            "Phone": "7809326245",
        }
        self.assertDictEqual(expected, ret)

    def test_ship_create_address_destination(self) -> None:
        """
        Test create address for rate formatting.
        """

        ret = self.order_ship._create_address(key="destination")
        expected = {
            "ContactName": "TESTING INC TWO",
            "CompanyName": "KENNETH CARMICHAEL",
            "AddressLine1": "140 Thad Johnson Road",
            "AddressLine2": "",
            "City": "TEST",
            "State": "AB",
            "PostalCode": "T9E 0V6",
            "Country": "CA",
            "Email": "customerservice@ubbe.com",
            "Phone": "7809326245",
        }
        self.assertDictEqual(expected, ret)

    def test_ship_create_pickup(self) -> None:
        """
        Test create pickup for rate formatting.
        """

        ret = self.order_ship._create_pickup()
        expected = {
            "EarliestTime": "2021-09-08T14:00:00+00:00",
            "LatestTime": "2021-09-08T22:30:00+00:00",
        }
        self.assertDictEqual(expected, ret)

    def test_ship_create_items(self) -> None:
        """
        Test create Package items for rate formatting.
        """
        description = ""
        description, packages = self.order_ship._create_items(description=description)
        expected = [
            {
                "Description": "TEST",
                "Length": Decimal("4.17"),
                "Width": Decimal("4.17"),
                "Height": Decimal("4.17"),
                "Weight": Decimal("23.37"),
            }
        ]
        self.assertListEqual(expected, packages)
        self.assertEqual("\nTEST\n1 - 4.17x4.17x4.17 @ 23.37", description)

    def test_ship_create_order(self) -> None:
        """
        Test Create Order for rate formatting.
        """

        ret = self.order_ship.create_order(customer="TEST1", price_set="TEST2")
        expected = {
            "Customer": "TEST1",
            "PriceSet": "TEST2",
            "CustomerContact": {
                "CustomerID": "TEST1",
                "Name": "Customer Service",
                "Email": "customerservice@ubbe.ca",
                "Phone": "8884206926",
            },
            "Items": [
                {
                    "Description": "TEST",
                    "Length": Decimal("4.17"),
                    "Width": Decimal("4.17"),
                    "Height": Decimal("4.17"),
                    "Weight": Decimal("23.37"),
                }
            ],
            "CollectionLocation": {
                "ContactName": "TESTING INC TWO",
                "CompanyName": "BBE Ottawa",
                "AddressLine1": "1540 Airport Road",
                "AddressLine2": "",
                "City": "Edmonton International Airport",
                "State": "AB",
                "PostalCode": "T9E 0V6",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "Phone": "7809326245",
            },
            "DeliveryLocation": {
                "ContactName": "TESTING INC TWO",
                "CompanyName": "KENNETH CARMICHAEL",
                "AddressLine1": "140 Thad Johnson Road",
                "AddressLine2": "",
                "City": "TEST",
                "State": "AB",
                "PostalCode": "T9E 0V6",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "Phone": "7809326245",
            },
            "CollectionArrivalWindow": {
                "EarliestTime": "2021-09-08T14:00:00+00:00",
                "LatestTime": "2021-09-08T22:30:00+00:00",
            },
            "RequestedBy": "ubbe (BBE Expediting Ltd)",
            "Description": "ub0334041338M\nSOMEREF/SOMEREF: \nTEST\n1 - 4.17x4.17x4.17 @ 23.37",
            "CollectionSignatureRequired": True,
            "DeliverySignatureRequired": True,
            "ReferenceNumber": "SOMEREF/SOMEREF",
            "PurchaseOrderNumber": "ub0334041338M",
            "Comments": "",
            "Weight": Decimal("468"),
            "Quantity": Decimal("2"),
            "PriceModifiers": [],
        }
        self.assertDictEqual(expected, ret)

    def test_ship_create_order_awb(self) -> None:
        """
        Test Create Order for rate formatting.
        """
        self.order_ship._ubbe_request["awb"] = "123456789"
        ret = self.order_ship.create_order(customer="TEST1", price_set="TEST2")
        expected = {
            "Customer": "TEST1",
            "PriceSet": "TEST2",
            "CustomerContact": {
                "CustomerID": "TEST1",
                "Name": "Customer Service",
                "Email": "customerservice@ubbe.ca",
                "Phone": "8884206926",
            },
            "Items": [
                {
                    "Description": "TEST",
                    "Length": Decimal("4.17"),
                    "Width": Decimal("4.17"),
                    "Height": Decimal("4.17"),
                    "Weight": Decimal("23.37"),
                }
            ],
            "CollectionLocation": {
                "ContactName": "TESTING INC TWO",
                "CompanyName": "BBE Ottawa",
                "AddressLine1": "1540 Airport Road",
                "AddressLine2": "",
                "City": "Edmonton International Airport",
                "State": "AB",
                "PostalCode": "T9E 0V6",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "Phone": "7809326245",
            },
            "DeliveryLocation": {
                "ContactName": "TESTING INC TWO",
                "CompanyName": "KENNETH CARMICHAEL",
                "AddressLine1": "140 Thad Johnson Road",
                "AddressLine2": "",
                "City": "TEST",
                "State": "AB",
                "PostalCode": "T9E 0V6",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "Phone": "7809326245",
            },
            "CollectionArrivalWindow": {
                "EarliestTime": "2021-09-08T14:00:00+00:00",
                "LatestTime": "2021-09-08T22:30:00+00:00",
            },
            "RequestedBy": "ubbe (BBE Expediting Ltd)",
            "Description": "ub0334041338M\n123456789/SOMEREF: \nTEST\n1 - 4.17x4.17x4.17 @ 23.37",
            "CollectionSignatureRequired": True,
            "DeliverySignatureRequired": True,
            "ReferenceNumber": "123456789/SOMEREF",
            "PurchaseOrderNumber": "ub0334041338M",
            "Comments": "",
            "Weight": Decimal("468"),
            "Quantity": Decimal("2"),
            "PriceModifiers": [],
        }
        self.assertDictEqual(expected, ret)
