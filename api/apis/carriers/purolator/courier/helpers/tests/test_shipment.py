"""
    Title: Purolator Address Helper Unit Tests
    Description: Unit Tests for the Purolator Address Helpers. Test Everything.
    Created: November 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.courier.helpers.shipment import PurolatorShipment
from api.models import SubAccount, Carrier, CarrierAccount


class PurolatorShipmentTests(TestCase):
    # TODO ADD different country phone numbers
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
        carrier = Carrier.objects.get(code=11)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request_rate = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "name": "Kenneth Carmichael",
                "phone": "7809326245",
                "email": "kcarmichael@bbex.com",
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "Edmonton",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
                "has_shipping_bays": True,
                "name": "Kenneth Carhael",
                "phone": "7808908614",
                "email": "kcarmichael@bbex.com",
            },
            "packages": [
                {
                    "quantity": 1,
                    "length": "100",
                    "width": "50",
                    "height": "50",
                    "weight": "50",
                    "package_type": "BOX",
                }
            ],
            "is_international": False,
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    11: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self._puro_shipment_rate = PurolatorShipment(
            ubbe_request=self.request_rate, is_rate=True
        )
        self._puro_shipment_ship = PurolatorShipment(
            ubbe_request=self.request_rate, is_rate=False
        )

    def test_build_payment(self):
        billing = self._puro_shipment_rate._build_payment(account_number="T9E0V6")

        expected = {
            "PaymentType": "Sender",
            "RegisteredAccountNumber": "T9E0V6",
            "BillingAccountNumber": "T9E0V6",
        }
        self.assertDictEqual(expected, billing)

    def test_build_payment_one(self):
        billing = self._puro_shipment_rate._build_payment(account_number="9999999999")

        expected = {
            "PaymentType": "Sender",
            "RegisteredAccountNumber": "9999999999",
            "BillingAccountNumber": "9999999999",
        }
        self.assertDictEqual(expected, billing)

    def test_build_payment_two(self):
        billing = self._puro_shipment_rate._build_payment(
            account_number="jksdckbsjcksnl"
        )

        expected = {
            "PaymentType": "Sender",
            "RegisteredAccountNumber": "jksdckbsjcksnl",
            "BillingAccountNumber": "jksdckbsjcksnl",
        }
        self.assertDictEqual(expected, billing)

    def test_build_payment_three(self):
        billing = self._puro_shipment_rate._build_payment(account_number="dksankndndnd")

        expected = {
            "PaymentType": "Sender",
            "RegisteredAccountNumber": "dksankndndnd",
            "BillingAccountNumber": "dksankndndnd",
        }
        self.assertDictEqual(expected, billing)

    def test_build_address_origin(self):
        address = self._puro_shipment_rate._build_address(
            address=self.request_rate["origin"], is_tax=True
        )

        expected = {
            "Address": {
                "Name": "Kenneth Carmichael",
                "Company": "BBE Ottawa",
                "StreetNumber": "1540",
                "StreetName": "Airport Road",
                "StreetType": "Road",
                "StreetAddress2": "",
                "City": "Edmonton International Airport",
                "Province": "AB",
                "Country": "CA",
                "PostalCode": "T9E0V6",
            },
            "TaxNumber": "",
        }
        self.assertDictEqual(expected, address)

    def test_build_address_destination(self):
        address = self._puro_shipment_rate._build_address(
            address=self.request_rate["destination"], is_tax=True
        )

        expected = {
            "Address": {
                "Name": "Kenneth Carhael",
                "Company": "BBE Ottawa",
                "StreetNumber": "1540",
                "StreetName": "Airport Road",
                "StreetType": "Road",
                "StreetAddress2": "",
                "City": "Edmonton",
                "Province": "AB",
                "Country": "CA",
                "PostalCode": "T5T4R7",
            },
            "TaxNumber": "",
        }

        self.assertDictEqual(expected, address)

    def test_build_tracking_reference(self):
        refs = self._puro_shipment_rate._build_tracking_reference()

        expected = {
            "Reference1": "",
            "Reference2": "",
            "Reference3": "",
            "Reference4": "",
        }

        self.assertDictEqual(expected, refs)

    def test_build_tracking_reference_numbers(self):
        copied = copy.deepcopy(self.request_rate)
        copied["order_number"] = "Test 1"
        copied["reference_one"] = "Test 2"
        copied["reference_two"] = "Test 3"
        copied["project"] = "Test 4"

        puro_shipment_rate = PurolatorShipment(ubbe_request=copied, is_rate=True)
        refs = puro_shipment_rate._build_tracking_reference()

        expected = {
            "Reference1": "Test 1/Test 2",
            "Reference2": "Test 2",
            "Reference3": "Test 3",
            "Reference4": "Test 4",
        }

        self.assertDictEqual(expected, refs)

    def test_build_content_detail(self):
        copied = copy.deepcopy(self.request_rate)
        copied["commodities"] = [
            {
                "quantity": 1,
                "unit_value": "10.0",
                "description": "Some Goods",
                "total_weight": "50",
                "made_in_country_code": "CA",
                "quantity_unit_of_measure": "EA",
            }
        ]
        puro_shipment_rate = PurolatorShipment(ubbe_request=copied, is_rate=True)
        inter = puro_shipment_rate._build_content_detail()

        expected = [
            {
                "Description": "Some Goods",
                "CountryOfManufacture": "CA",
                "UnitValue": "10.0",
                "Quantity": 1,
                "USMCADocumentIndicator": False,
                "TextileIndicator": False,
                "TextileManufacturer": "",
                "FCCDocumentIndicator": False,
                "SenderIsProducerIndicator": False,
            }
        ]

        self.assertListEqual(expected, inter)

    def test_build_international(self):
        copied = copy.deepcopy(self.request_rate)
        copied["broker"] = {
            "address": "1540 Airport Road",
            "city": "Edmonton",
            "company_name": "BBE Ottawa",
            "country": "CA",
            "postal_code": "T5T4R7",
            "province": "AB",
            "has_shipping_bays": True,
            "phone": "7808908614",
            "email": "kcarmichael@bbex.com",
        }

        inter = self._puro_shipment_rate._build_international(copied["broker"])
        expected = {
            "DutyInformation": {
                "BillDutiesToParty": "Receiver",
                "BusinessRelationship": "NotRelated",
                "Currency": "CAD",
            },
            "PreferredCustomsBroker": "BBE Ottawa",
            "DocumentsOnlyIndicator": True,
            "ImportExportType": "Permanent",
            "CustomsInvoiceDocumentIndicator": False,
        }

        self.assertDictEqual(expected, inter)

    def test_shipment(self):
        ship = self._puro_shipment_rate.shipment(account_number="dsavadsffwef")

        expected = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": {
                "Address": {
                    "Name": "Kenneth Carmichael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton International Airport",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T9E0V6",
                },
                "TaxNumber": "",
            },
            "ReceiverInformation": {
                "Address": {
                    "Name": "Kenneth Carhael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T5T4R7",
                },
                "TaxNumber": "",
            },
            "PackageInformation": {
                "ServiceID": "PurolatorExpress",
                "Description": "Package",
                "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                "TotalPieces": Decimal("1"),
                "PiecesInformation": {
                    "Piece": [
                        {
                            "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Options": [],
                        }
                    ]
                },
            },
            "TrackingReferenceInformation": {
                "Reference1": "",
                "Reference2": "",
                "Reference3": "",
                "Reference4": "",
            },
            "PaymentInformation": {
                "PaymentType": "Sender",
                "RegisteredAccountNumber": "dsavadsffwef",
                "BillingAccountNumber": "dsavadsffwef",
            },
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": ""},
        }

        self.assertDictEqual(expected, ship)

    def test_shipment_multiple(self):
        copied = copy.deepcopy(self.request_rate)
        copied["order_number"] = "Test 1"
        copied["reference_one"] = "Test 2"
        copied["reference_two"] = "Test 3"
        copied["project"] = "Test 4"

        copied["packages"].append(
            {
                "quantity": 2,
                "length": "80",
                "width": "30",
                "height": "30",
                "weight": "30",
                "package_type": "BOX",
            }
        )

        puro_shipment_rate = PurolatorShipment(ubbe_request=copied, is_rate=True)
        ship = puro_shipment_rate.shipment(account_number="dsavadsffwef")

        expected = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": {
                "Address": {
                    "Name": "Kenneth Carmichael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton International Airport",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T9E0V6",
                },
                "TaxNumber": "",
            },
            "ReceiverInformation": {
                "Address": {
                    "Name": "Kenneth Carhael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T5T4R7",
                },
                "TaxNumber": "",
            },
            "PackageInformation": {
                "ServiceID": "PurolatorExpress",
                "Description": "Package Package",
                "TotalWeight": {"Value": Decimal("80"), "WeightUnit": "kg"},
                "TotalPieces": Decimal("3"),
                "PiecesInformation": {
                    "Piece": [
                        {
                            "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Options": [],
                        },
                        {
                            "Weight": {"Value": Decimal("30"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("80"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                            "Options": [],
                        },
                        {
                            "Weight": {"Value": Decimal("30"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("80"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("30"), "DimensionUnit": "cm"},
                            "Options": [],
                        },
                    ]
                },
            },
            "TrackingReferenceInformation": {
                "Reference1": "Test 1/Test 2",
                "Reference2": "Test 2",
                "Reference3": "Test 3",
                "Reference4": "Test 4",
            },
            "PaymentInformation": {
                "PaymentType": "Sender",
                "RegisteredAccountNumber": "dsavadsffwef",
                "BillingAccountNumber": "dsavadsffwef",
            },
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": ""},
        }

        self.assertDictEqual(expected, ship)

    def test_shipment_service(self):
        copied = copy.deepcopy(self.request_rate)
        copied["order_number"] = "Test 1"
        copied["reference_one"] = "Test 2"
        copied["reference_two"] = "Test 3"
        copied["project"] = "Test 4"

        copied["service"] = {"service_code": "PurolatorExpress9AM"}

        puro_shipment = PurolatorShipment(ubbe_request=copied, is_rate=True)
        ship = puro_shipment.shipment(account_number="dsavadsffwef")

        expected = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": {
                "Address": {
                    "Name": "Kenneth Carmichael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton International Airport",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T9E0V6",
                },
                "TaxNumber": "",
            },
            "ReceiverInformation": {
                "Address": {
                    "Name": "Kenneth Carhael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T5T4R7",
                },
                "TaxNumber": "",
            },
            "PackageInformation": {
                "ServiceID": "PurolatorExpress",
                "Description": "Package",
                "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                "TotalPieces": Decimal("1"),
                "PiecesInformation": {
                    "Piece": [
                        {
                            "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Options": [],
                        }
                    ]
                },
            },
            "TrackingReferenceInformation": {
                "Reference1": "Test 1/Test 2",
                "Reference2": "Test 2",
                "Reference3": "Test 3",
                "Reference4": "Test 4",
            },
            "PaymentInformation": {
                "PaymentType": "Sender",
                "RegisteredAccountNumber": "dsavadsffwef",
                "BillingAccountNumber": "dsavadsffwef",
            },
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": ""},
        }

        self.assertDictEqual(expected, ship)

    def test_shipment_service_service_code(self):
        copied = copy.deepcopy(self.request_rate)
        copied["order_number"] = "Test 1"
        copied["reference_one"] = "Test 2"
        copied["reference_two"] = "Test 3"
        copied["project"] = "Test 4"
        copied["service_code"] = "PurolatorExpress"

        puro_shipment = PurolatorShipment(ubbe_request=copied, is_rate=True)
        ship = puro_shipment.shipment(account_number="dsavadsffwef")

        expected = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": {
                "Address": {
                    "Name": "Kenneth Carmichael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton International Airport",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T9E0V6",
                },
                "TaxNumber": "",
            },
            "ReceiverInformation": {
                "Address": {
                    "Name": "Kenneth Carhael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T5T4R7",
                },
                "TaxNumber": "",
            },
            "PackageInformation": {
                "ServiceID": "PurolatorExpress",
                "Description": "Package",
                "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                "TotalPieces": Decimal("1"),
                "PiecesInformation": {
                    "Piece": [
                        {
                            "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Options": [],
                        }
                    ]
                },
            },
            "TrackingReferenceInformation": {
                "Reference1": "Test 1/Test 2",
                "Reference2": "Test 2",
                "Reference3": "Test 3",
                "Reference4": "Test 4",
            },
            "PaymentInformation": {
                "PaymentType": "Sender",
                "RegisteredAccountNumber": "dsavadsffwef",
                "BillingAccountNumber": "dsavadsffwef",
            },
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": ""},
        }

        self.assertDictEqual(expected, ship)

    def test_shipment_service_ship(self):
        copied = copy.deepcopy(self.request_rate)
        copied["order_number"] = "Test 1"
        copied["reference_one"] = "Test 2"
        copied["reference_two"] = "Test 3"
        copied["project"] = "Test 4"

        copied["service"] = {"service_code": "PurolatorExpress9AM"}

        puro_shipment = PurolatorShipment(ubbe_request=copied, is_rate=False)
        ship = puro_shipment.shipment(account_number="dsavadsffwef")

        expected = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": {
                "Address": {
                    "Name": "Kenneth Carmichael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton International Airport",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T9E0V6",
                    "PhoneNumber": {
                        "CountryCode": 1,
                        "AreaCode": "780",
                        "Phone": "9326245",
                        "Extension": "",
                    },
                },
                "TaxNumber": "",
            },
            "ReceiverInformation": {
                "Address": {
                    "Name": "Kenneth Carhael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T5T4R7",
                    "PhoneNumber": {
                        "CountryCode": 1,
                        "AreaCode": "780",
                        "Phone": "8908614",
                        "Extension": "",
                    },
                },
                "TaxNumber": "",
            },
            "PackageInformation": {
                "ServiceID": "PurolatorExpress",
                "Description": "Package",
                "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                "TotalPieces": Decimal("1"),
                "PiecesInformation": {
                    "Piece": [
                        {
                            "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Options": [],
                        }
                    ]
                },
            },
            "TrackingReferenceInformation": {
                "Reference1": "Test 1/Test 2",
                "Reference2": "Test 2",
                "Reference3": "Test 3",
                "Reference4": "Test 4",
            },
            "PaymentInformation": {
                "PaymentType": "Sender",
                "RegisteredAccountNumber": "dsavadsffwef",
                "BillingAccountNumber": "dsavadsffwef",
            },
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": ""},
        }
        self.assertDictEqual(expected, ship)

    def test_shipment_service_ship_international(self):
        copied = copy.deepcopy(self.request_rate)
        copied["is_international"] = True
        copied["order_number"] = "Test 1"
        copied["reference_one"] = "Test 2"
        copied["reference_two"] = "Test 3"
        copied["project"] = "Test 4"
        copied["broker"] = {
            "address": "1540 Airport Road",
            "city": "Edmonton",
            "company_name": "BBE Ottawa",
            "country": "CA",
            "postal_code": "T5T4R7",
            "province": "AB",
            "has_shipping_bays": True,
            "phone": "7808908614",
            "email": "kcarmichael@bbex.com",
        }

        copied["service"] = {"service_code": "PurolatorExpress9AM"}

        puro_shipment = PurolatorShipment(ubbe_request=copied, is_rate=False)
        ship = puro_shipment.shipment(account_number="dsavadsffwef")

        expected = {
            "ShipmentDate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "SenderInformation": {
                "Address": {
                    "Name": "Kenneth Carmichael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton International Airport",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T9E0V6",
                    "PhoneNumber": {
                        "CountryCode": 1,
                        "AreaCode": "780",
                        "Phone": "9326245",
                        "Extension": "",
                    },
                },
                "TaxNumber": "",
            },
            "ReceiverInformation": {
                "Address": {
                    "Name": "Kenneth Carhael",
                    "Company": "BBE Ottawa",
                    "StreetNumber": "1540",
                    "StreetName": "Airport Road",
                    "StreetType": "Road",
                    "StreetAddress2": "",
                    "City": "Edmonton",
                    "Province": "AB",
                    "Country": "CA",
                    "PostalCode": "T5T4R7",
                    "PhoneNumber": {
                        "CountryCode": 1,
                        "AreaCode": "780",
                        "Phone": "8908614",
                        "Extension": "",
                    },
                },
                "TaxNumber": "",
            },
            "PackageInformation": {
                "ServiceID": "PurolatorExpressU.S.",
                "Description": "Package",
                "TotalWeight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                "TotalPieces": Decimal("1"),
                "PiecesInformation": {
                    "Piece": [
                        {
                            "Weight": {"Value": Decimal("50"), "WeightUnit": "kg"},
                            "Length": {"Value": Decimal("100"), "DimensionUnit": "cm"},
                            "Width": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Height": {"Value": Decimal("50"), "DimensionUnit": "cm"},
                            "Options": [],
                        }
                    ]
                },
            },
            "TrackingReferenceInformation": {
                "Reference1": "Test 1/Test 2",
                "Reference2": "Test 2",
                "Reference3": "Test 3",
                "Reference4": "Test 4",
            },
            "PaymentInformation": {
                "PaymentType": "Sender",
                "RegisteredAccountNumber": "dsavadsffwef",
                "BillingAccountNumber": "dsavadsffwef",
            },
            "PickupInformation": {"PickupType": "PreScheduled"},
            "NotificationInformation": {
                "ConfirmationEmailAddress": "no-reply@ubbe.com",
                "AdvancedShippingNotificationEmailAddress1": "no-reply@ubbe.com",
            },
            "OtherInformation": {"SpecialInstructions": ""},
            "InternationalInformation": {
                "DutyInformation": {
                    "BillDutiesToParty": "Receiver",
                    "BusinessRelationship": "NotRelated",
                    "Currency": "CAD",
                },
                "PreferredCustomsBroker": "BBE Ottawa",
                "DocumentsOnlyIndicator": True,
                "ImportExportType": "Permanent",
                "CustomsInvoiceDocumentIndicator": False,
            },
        }
        self.assertDictEqual(expected, ship)
