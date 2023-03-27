"""
    Title: TwoShip Rate Unit Tests
    Description: Unit Tests for the TwoShip Rate. Test Everything.
    Created: January 23, 2023
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.twoship.endpoints.twoship_ship_v2 import TwoShipShip
from api.globals.carriers import UPS, DHL
from api.models import SubAccount, Carrier, CarrierAccount


class TwoShipRateTests(TestCase):
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
        sub_account = SubAccount.objects.get(is_default=True)
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=UPS)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "carrier_id": UPS,
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
                "date": datetime.datetime.strptime("2023-01-23", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "packages": [
                {
                    "description": "Test",
                    "package_type": "SKID",
                    "freight_class": "70.00",
                    "quantity": 1,
                    "length": Decimal("48"),
                    "width": Decimal("48"),
                    "height": Decimal("48"),
                    "weight": Decimal("100"),
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
                    UPS: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
            "service_code": "STD",
            "service_name": "Express",
            "order_number": "UB1234567890",
            "is_metric": True,
            "is_international": False,
            "is_dangerous_goods": False,
            "special_instructions": "test test test",
            "reference_one": "HI am a test",
            "commodities": [
                {
                    "quantity": 1,
                    "unit_value": Decimal("10.00"),
                    "description": "Air Jordan",
                    "total_weight": Decimal("100.00"),
                    "made_in_country_code": "CA",
                }
            ],
        }

        self._two_response = {
            "ShipDocuments": [
                {
                    "Type": 0,
                    "Href": "https://ship.2ship.com/BBE/pdfs/2023_01_12/333922063487.93c37a07-1d5d-4963-829b-87319a80906b.pdf",
                    "DocumentBase64String": "J",
                    "Encoding": 0,
                    "WarningMessage": None,
                    "DocumentName": "Label",
                    "AutoPrintUrl": "",
                    "Size": 0,
                }
            ],
            "ShipId": 26990271,
            "OrderNumber": "GO1479105307M",
            "CloseAggregationId": None,
            "Service": {
                "CarrierId": 11,
                "SCAC": "",
                "CarrierName": "Purolator",
                "ERROR": None,
                "Service": {
                    "Name": "Purolator Ground®",
                    "Code": "260",
                    "ServiceGroups": None,
                    "DeliveryServiceGroups": None,
                    "GroupsShipmentOptions": None,
                    "PerformanceScore": 0.0,
                    "DeliveryPerformanceOnTimePercentage": 0.0,
                },
                "TransitDays": 4,
                "DeliveryDate": "2023-01-18T23:59:00Z",
                "AverageListPrice": 0.0,
                "ListPrice": {
                    "DimensionalWeight": 0.0,
                    "BilledWeight": 20.00,
                    "WeightType": 1,
                    "Freight": 107.880,
                    "Fuel": {"Percentage": 0.375, "Amount": 40.340},
                    "TotalSurcharges": 4.950,
                    "Surcharges": [
                        {
                            "Code": None,
                            "Name": "Residential Area",
                            "AffectsFuel": False,
                            "Amount": 4.45,
                        },
                        {
                            "Code": None,
                            "Name": "Peak Residential",
                            "AffectsFuel": False,
                            "Amount": 0.50,
                        },
                    ],
                    "TotalTaxes": 7.660,
                    "Taxes": [{"Name": "GST", "Percentage": 5.0, "Amount": 7.660}],
                    "Total": 160.830,
                    "Currency": "CAD",
                    "OnlinePaymentFee": 0.0,
                    "TransactionFee": 0.0,
                    "PickupFee": 0.0,
                    "TotalPriceInSelectedCurrency": 160.830,
                    "PackagePrices": [
                        {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 20.00,
                            "WeightType": 1,
                            "Freight": 107.880,
                            "Fuel": {"Percentage": 0.375, "Amount": 40.340},
                            "TotalSurcharges": 4.950,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Residential Area",
                                    "AffectsFuel": False,
                                    "Amount": 4.45,
                                },
                                {
                                    "Code": None,
                                    "Name": "Peak Residential",
                                    "AffectsFuel": False,
                                    "Amount": 0.50,
                                },
                            ],
                            "TotalTaxes": 7.660,
                            "Taxes": [
                                {"Name": "GST", "Percentage": 5.0, "Amount": 7.660}
                            ],
                            "Total": 160.830,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.0,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                        }
                    ],
                },
                "ClientPrice": {
                    "DimensionalWeight": 0.0,
                    "BilledWeight": 20.00,
                    "WeightType": 1,
                    "Freight": 37.760000000,
                    "Fuel": {"Percentage": 0.400, "Amount": 15.104000000000},
                    "TotalSurcharges": 4.450,
                    "Surcharges": [
                        {
                            "Code": None,
                            "Name": "Residential Area",
                            "AffectsFuel": False,
                            "Amount": 4.45,
                        }
                    ],
                    "TotalTaxes": 2.865700000000,
                    "Taxes": [
                        {"Name": "GST", "Percentage": 5.0, "Amount": 2.865700000000}
                    ],
                    "Total": 60.179700000000,
                    "Currency": "CAD",
                    "OnlinePaymentFee": 0.00,
                    "TransactionFee": 0.0,
                    "PickupFee": 0.00,
                    "TotalPriceInSelectedCurrency": 60.179700000000,
                    "PackagePrices": [
                        {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 20.00,
                            "WeightType": 1,
                            "Freight": 37.760000000,
                            "Fuel": {"Percentage": 0.400, "Amount": 15.104000000000},
                            "TotalSurcharges": 4.450,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Residential Area",
                                    "AffectsFuel": False,
                                    "Amount": 4.45,
                                }
                            ],
                            "TotalTaxes": 2.865700000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 2.865700000000,
                                }
                            ],
                            "Total": 60.179700000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.00,
                        }
                    ],
                },
                "CustomerPrice": {
                    "DimensionalWeight": 0.0,
                    "BilledWeight": 20.00,
                    "WeightType": 1,
                    "Freight": 37.760000000,
                    "Fuel": {"Percentage": 0.400, "Amount": 15.104000000000},
                    "TotalSurcharges": 4.450,
                    "Surcharges": [
                        {
                            "Code": None,
                            "Name": "Residential Area",
                            "AffectsFuel": False,
                            "Amount": 4.45,
                        }
                    ],
                    "TotalTaxes": 2.86570000000000,
                    "Taxes": [
                        {"Name": "GST", "Percentage": 5.0, "Amount": 2.86570000000000}
                    ],
                    "Total": 60.17970000000000,
                    "Currency": "CAD",
                    "OnlinePaymentFee": 0.00,
                    "TransactionFee": 0.0,
                    "PickupFee": 0.0,
                    "TotalPriceInSelectedCurrency": 60.17970000000000,
                    "PackagePrices": [
                        {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 20.00,
                            "WeightType": 1,
                            "Freight": 37.760000000,
                            "Fuel": {"Percentage": 0.400, "Amount": 15.104000000000},
                            "TotalSurcharges": 4.450,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Residential Area",
                                    "AffectsFuel": False,
                                    "Amount": 4.45,
                                }
                            ],
                            "TotalTaxes": 2.86570000000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 2.86570000000000,
                                }
                            ],
                            "Total": 60.17970000000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                        }
                    ],
                },
                "OriginRateZone": "(ALL)",
                "DestinationRateZone": "D11",
            },
            "Carrier": {
                "Id": 11,
                "SCAC": "",
                "Name": "Purolator",
                "Type": 0,
                "BillingAccount": "9999085",
            },
            "LocationId": 4110,
            "LocationName": "YEGFF",
            "ProNumber": "",
            "TrackingNumber": "333922063487",
            "TrackingUrl": "https://ship.2ship.com/Tracking/Index?TrackingNumber=333922063487&Carrier=11&SId=26990271",
            "AirwayBillNumber": "",
            "PackageTrackingNumbers": ["333922063487"],
            "ShipmentDetails": {
                "ShipDate": "2023-01-12T00:00:00",
                "Packages": [
                    {
                        "Weight": 20.0,
                        "Width": 20.0,
                        "Length": 20.0,
                        "Height": 20.0,
                        "FreightClassId": 50.0,
                        "NMFCItem": None,
                        "NMFCSub": None,
                        "WeightType": 1,
                        "DimensionType": 1,
                        "DimensionCode": None,
                        "Packaging": 1,
                        "InsuranceAmount": 0.0,
                        "InsuranceCurrency": None,
                        "Reference1": None,
                        "Reference2": None,
                        "PONumber": None,
                        "NumberOfPiecesInSkid": 1,
                        "SkidDescription": "PARTs",
                        "OriginalWeight": 0.0,
                        "ShipmentId": "GO1479105307M",
                        "InvoiceNo": None,
                        "IsStackable": False,
                        "OnHoldAggregatedOrderNumber": None,
                        "LicencePlate": None,
                        "PreAssignTrackingNumber": None,
                        "ApplyWeightAndDimsFromTheAssignedCommodity": False,
                    }
                ],
                "ShipmentReference": "FF034925",
                "ShipmentReference2": None,
                "ShipmentPONumber": None,
                "Sender": {
                    "Id": None,
                    "PersonName": "KENNETH",
                    "CompanyName": "BBE",
                    "Country": "CA",
                    "State": "ON",
                    "City": "Ottawa",
                    "PostalCode": "K1V0R4",
                    "Address1": "140 Thad Johnson Private",
                    "Address2": None,
                    "Address3": None,
                    "Telephone": "7809326245",
                    "TelephoneExtension": None,
                    "Email": "kcarmichael@bbex.com",
                    "IsResidential": False,
                    "TaxID": None,
                    "RecipientType": None,
                    "AccountNo": None,
                },
                "Recipient": {
                    "Id": None,
                    "PersonName": "Kenneth Carmichael",
                    "CompanyName": "Kenneth Carmichael",
                    "Country": "CA",
                    "State": "AB",
                    "City": "Edmonton International Airport",
                    "PostalCode": "T5T4R7",
                    "Address1": "8812 218 St NW",
                    "Address2": None,
                    "Address3": None,
                    "Telephone": "7809326245",
                    "TelephoneExtension": None,
                    "Email": "kcarmichael@bbex.com",
                    "IsResidential": False,
                    "TaxID": None,
                    "RecipientType": None,
                    "AccountNo": None,
                },
                "ConsolidationUnit": {"ConsolidationUnitId": 0},
                "PickupNumber": "",
                "PickupCarrierLocationCode": "",
                "PickupErrorMessage": "",
                "Contents": None,
                "Billing": None,
                "GLCategory": None,
                "GLSubCategory": None,
                "DepartmentDescription": None,
                "DepartmentCode": None,
                "AggregatedOrderNumbers": None,
                "AggregationId": None,
                "IsReturn": False,
                "OriginalShipmentInfo": None,
                "LabelGenerationDate": "2023-01-11T12:33:51.7384336-05:00",
                "ExternalOrderIdentifier": None,
                "AggregatedExternalOrderIdentifiers": None,
            },
            "ExchangeRate": None,
            "MycarrierDetails": None,
            "Status": "Shipped",
            "StatusTimestamp": None,
            "QRCodeValue": None,
            "QRCodeImageURL": None,
            "ClientId": 2158,
            "ExternalClientID": "",
            "UserId": 0,
            "UserName": None,
            "WebsiteUrl": None,
            "OriginHubCode": "",
            "DestinationHubCode": "",
            "InternalNotes": None,
            "ShipWithoutPrinterMessage": "",
        }

        self._two_ship = TwoShipShip(ubbe_request=self.request)

    def test_build_packages(self):
        """
        Test TwoShip ship package building
        :return:
        """

        ret = self._two_ship._build_packages()
        expected = [
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 1,
                "WeightType": 1,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            }
        ]
        self.assertListEqual(expected, ret)

    def test_build_packages_quantity(self):
        """
        Test TwoShip ship package building
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["packages"][0]["quantity"] = 5

        ret = TwoShipShip(ubbe_request=copied)._build_packages()
        expected = [
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 1,
                "WeightType": 1,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            },
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 1,
                "WeightType": 1,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            },
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 1,
                "WeightType": 1,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            },
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 1,
                "WeightType": 1,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            },
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 1,
                "WeightType": 1,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            },
        ]
        self.assertListEqual(expected, ret)

    def test_build_packages_quantity_imperial(self):
        """
        Test TwoShip ship package building
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["is_metric"] = False

        ret = TwoShipShip(ubbe_request=copied)._build_packages()
        expected = [
            {
                "Packaging": 1,
                "SkidDescription": "Test",
                "Length": Decimal("48"),
                "Width": Decimal("48"),
                "Height": Decimal("48"),
                "Weight": Decimal("100"),
                "FreightClassId": "70.00",
                "DimensionType": 0,
                "WeightType": 0,
                "ShipmentId": "UB1234567890",
                "Reference1": "HI am a test",
                "Reference2": "",
            }
        ]
        self.assertListEqual(expected, ret)

    def test_build_reference(self):
        """
        Test TwoShip ship references
        :return:
        """

        ret = self._two_ship._build_reference()
        expected = {"ShipmentReference": "HI am a test", "ShipmentReference2": ""}
        self.assertDictEqual(expected, ret)

    def test_build_reference_two(self):
        """
        Test TwoShip ship references two
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Ref One"
        copied["reference_two"] = "Ref Two"

        ret = TwoShipShip(ubbe_request=copied)._build_reference()
        expected = {"ShipmentReference": "Ref One", "ShipmentReference2": "Ref Two"}
        self.assertDictEqual(expected, ret)

    def test_build_reference_awb(self):
        """
        Test TwoShip ship references awb
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["reference_one"] = "Ref One"
        copied["reference_two"] = "Ref Two"
        copied["awb"] = "518-YEG-1234567"

        ret = TwoShipShip(ubbe_request=copied)._build_reference()
        expected = {
            "ShipmentReference": "AWB 518-YEG-1234567:Ref One",
            "ShipmentReference2": "Ref Two",
        }

        self.assertDictEqual(expected, ret)

    def test_build_international(self):
        """
        Test TwoShip ship international.
        :return:
        """

        ret = self._two_ship._build_international()
        expected = {
            "CustomsBillingOptions": {"BillingType": 2},
            "Invoice": {"TermsOfSale": 5, "Purpose": 1, "Currency": "CAD"},
        }
        self.assertDictEqual(expected, ret)

    def test_build_international_broker(self):
        """
        Test TwoShip ship international broker.
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["broker"] = {
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
        }

        ret = TwoShipShip(ubbe_request=copied)._build_international()
        expected = {
            "CustomsBillingOptions": {"BillingType": 2},
            "Invoice": {"TermsOfSale": 5, "Purpose": 1, "Currency": "CAD"},
            "Broker": {
                "CompanyName": "BBE Ottawa",
                "Telephone": "7809326245",
                "Email": "developer@bbex.com",
                "Address1": "1540 Airport Road",
                "City": "Edmonton International Airport",
                "State": "AB",
                "Country": "CA",
                "PostalCode": "T9E0V6",
            },
        }
        self.assertDictEqual(expected, ret)

    def test_build_commodities(self):
        """
        Test TwoShip ship commodities
        :return:
        """

        ret = self._two_ship._build_commodities()
        expected = {
            "Commodities": [
                {
                    "Quantity": 1,
                    "UnitValue": Decimal("10.00"),
                    "Description": "Air Jordan",
                    "TotalWeight": Decimal("100.00"),
                    "MadeInCountryCode": "CA",
                    "QuantityUnitOfMeasure": "E",
                }
            ]
        }
        self.assertDictEqual(expected, ret)

    def test_build_request(self):
        """
        Test TwoShip ship request
        :return:
        """

        ret = self._two_ship._build_request()
        expected = {
            "Billing": {"BillingType": 1},
            "LocationId": 4110,
            "LocationName": "YEGFF",
            "RetrieveBase64StringDocuments": True,
            "CarrierId": 8,
            "ServiceCode": "STD",
            "OrderNumber": "UB1234567890",
            "Sender": {
                "Address1": "1540 Airport Road",
                "Address2": "",
                "City": "edmonton international airport",
                "CompanyName": "BBE Ottawa",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "IsResidential": False,
                "PersonName": "BBE",
                "PostalCode": "T9E0V6",
                "State": "AB",
                "Telephone": "7809326245",
                "TelephoneExtension": "",
            },
            "Recipient": {
                "Address1": "140 THAD JOHNSON PRIV Suite 7",
                "Address2": "",
                "City": "ottawa",
                "CompanyName": "BBE Ottawa",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "IsResidential": False,
                "PersonName": "BBE",
                "PostalCode": "K1V0R1",
                "State": "ON",
                "Telephone": "7809326245",
                "TelephoneExtension": "",
            },
            "Packages": [
                {
                    "Packaging": 1,
                    "SkidDescription": "Test",
                    "Length": Decimal("48"),
                    "Width": Decimal("48"),
                    "Height": Decimal("48"),
                    "Weight": Decimal("100"),
                    "FreightClassId": "70.00",
                    "DimensionType": 1,
                    "WeightType": 1,
                    "ShipmentId": "UB1234567890",
                    "Reference1": "HI am a test",
                    "Reference2": "",
                }
            ],
            "LabelPrintPreferences": {"Encoding": 0, "OutputFormat": 1},
            "ShipmentInstructions": "test test test",
            "ShipmentReference": "HI am a test",
            "ShipmentReference2": "",
        }
        del ret["WS_Key"]

        self.assertDictEqual(expected, ret)

    def test_build_request_international(self):
        """
        Test TwoShip ship request international.
        :return:
        """

        copied = copy.deepcopy(self.request)
        copied["is_international"] = True

        ret = TwoShipShip(ubbe_request=copied)._build_request()
        expected = {
            "Billing": {"BillingType": 1},
            "LocationId": 4110,
            "LocationName": "YEGFF",
            "RetrieveBase64StringDocuments": True,
            "CarrierId": 8,
            "ServiceCode": "STD",
            "OrderNumber": "UB1234567890",
            "Sender": {
                "Address1": "1540 Airport Road",
                "Address2": "",
                "City": "edmonton international airport",
                "CompanyName": "BBE Ottawa",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "IsResidential": False,
                "PersonName": "BBE",
                "PostalCode": "T9E0V6",
                "State": "AB",
                "Telephone": "7809326245",
                "TelephoneExtension": "",
            },
            "Recipient": {
                "Address1": "140 THAD JOHNSON PRIV Suite 7",
                "Address2": "",
                "City": "ottawa",
                "CompanyName": "BBE Ottawa",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "IsResidential": False,
                "PersonName": "BBE",
                "PostalCode": "K1V0R1",
                "State": "ON",
                "Telephone": "7809326245",
                "TelephoneExtension": "",
            },
            "Packages": [
                {
                    "Packaging": 1,
                    "SkidDescription": "Test",
                    "Length": Decimal("48"),
                    "Width": Decimal("48"),
                    "Height": Decimal("48"),
                    "Weight": Decimal("100"),
                    "FreightClassId": "70.00",
                    "DimensionType": 1,
                    "WeightType": 1,
                    "ShipmentId": "UB1234567890",
                    "Reference1": "HI am a test",
                    "Reference2": "",
                }
            ],
            "LabelPrintPreferences": {"Encoding": 0, "OutputFormat": 1},
            "ShipmentInstructions": "test test test",
            "ShipmentReference": "HI am a test",
            "ShipmentReference2": "",
            "CustomsBillingOptions": {"BillingType": 2},
            "Invoice": {"TermsOfSale": 5, "Purpose": 1, "Currency": "CAD"},
            "InternationalOptions": {
                "CustomsBillingOptions": {"BillingType": 2},
                "Invoice": {"TermsOfSale": 5, "Purpose": 1, "Currency": "CAD"},
            },
            "Contents": {
                "Commodities": [
                    {
                        "Quantity": 1,
                        "UnitValue": Decimal("10.00"),
                        "Description": "Air Jordan",
                        "TotalWeight": Decimal("100.00"),
                        "MadeInCountryCode": "CA",
                        "QuantityUnitOfMeasure": "E",
                    }
                ]
            },
        }
        del ret["WS_Key"]

        self.assertDictEqual(expected, ret)

    def test_build_request_international_dhl(self):
        """
        Test TwoShip ship request international DHL.
        :return:
        """

        copied = copy.deepcopy(self.request)
        copied["carrier_id"] = DHL

        ret = TwoShipShip(ubbe_request=copied)._build_request()
        expected = {
            "Billing": {"BillingType": 1},
            "LocationId": 4110,
            "LocationName": "YEGFF",
            "RetrieveBase64StringDocuments": True,
            "CarrierId": 7,
            "ServiceCode": "STD",
            "OrderNumber": "UB1234567890",
            "Sender": {
                "Address1": "1540 Airport Road",
                "Address2": "",
                "City": "edmonton international airport",
                "CompanyName": "BBE Ottawa",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "IsResidential": False,
                "PersonName": "BBE",
                "PostalCode": "T9E0V6",
                "State": "AB",
                "Telephone": "7809326245",
                "TelephoneExtension": "",
            },
            "Recipient": {
                "Address1": "140 THAD JOHNSON PRIV Suite 7",
                "Address2": "",
                "City": "ottawa",
                "CompanyName": "BBE Ottawa",
                "Country": "CA",
                "Email": "customerservice@ubbe.com",
                "IsResidential": False,
                "PersonName": "BBE",
                "PostalCode": "K1V0R1",
                "State": "ON",
                "Telephone": "7809326245",
                "TelephoneExtension": "",
            },
            "Packages": [
                {
                    "Packaging": 1,
                    "SkidDescription": "Test",
                    "Length": Decimal("48"),
                    "Width": Decimal("48"),
                    "Height": Decimal("48"),
                    "Weight": Decimal("100"),
                    "FreightClassId": "70.00",
                    "DimensionType": 1,
                    "WeightType": 1,
                    "ShipmentId": "UB1234567890",
                    "Reference1": "HI am a test",
                    "Reference2": "",
                }
            ],
            "LabelPrintPreferences": {"Encoding": 0, "OutputFormat": 1},
            "ShipmentInstructions": "test test test",
            "ShipmentReference": "HI am a test",
            "ShipmentReference2": "",
        }
        del ret["WS_Key"]

        self.assertDictEqual(expected, ret)

    def test_format_response(self):
        """
        Test TwoShip ship response into ubbe
        :return:
        """

        ret = self._two_ship._format_response(response=self._two_response)
        expected = {
            "carrier_id": 8,
            "carrier_name": "Purolator",
            "service_code": "260",
            "service_name": "Purolator Ground®",
            "freight": Decimal("37.76"),
            "surcharges": [
                {
                    "name": "Residential Area",
                    "cost": Decimal("4.45"),
                    "percentage": Decimal("0.00"),
                },
                {
                    "name": "Fuel Surcharge",
                    "cost": Decimal("15.104"),
                    "percentage": Decimal("40.00"),
                },
            ],
            "surcharges_cost": Decimal("19.55"),
            "tax_percent": Decimal("5.00"),
            "taxes": Decimal("2.87"),
            "total": Decimal("60.18"),
            "tracking_number": "333922063487",
            "pickup_id": "",
            "transit_days": 4,
            "delivery_date": "2023-01-18T23:59:00Z",
            "carrier_api_id": 26990271,
            "documents": [{"document": "J", "type": "1"}],
        }
        self.assertDictEqual(expected, ret)
