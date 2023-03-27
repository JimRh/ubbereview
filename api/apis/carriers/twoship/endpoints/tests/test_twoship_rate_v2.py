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

from api.apis.carriers.twoship.endpoints.twoship_rate_v2 import TwoShipRate
from api.globals.carriers import UPS
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
            "carrier_id": [UPS],
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
            "special_instructions": "test test test",
        }

        self._two_response = [
            {
                "Carrier": {
                    "Id": 8,
                    "SCAC": "UPSG",
                    "Name": "UPS",
                    "Type": 0,
                    "BillingAccount": "81X843",
                },
                "DropOffLocations": None,
                "HoldForPickupLocations": None,
                "Services": [
                    {
                        "CarrierId": 8,
                        "SCAC": "UPSG",
                        "CarrierName": "UPS",
                        "ERROR": None,
                        "Service": {
                            "Name": "UPS Express®",
                            "Code": "01",
                            "ServiceGroups": [],
                            "DeliveryServiceGroups": None,
                            "GroupsShipmentOptions": None,
                            "PerformanceScore": 0.0,
                            "DeliveryPerformanceOnTimePercentage": 0.0,
                        },
                        "TransitDays": 1,
                        "DeliveryDate": "2023-01-24T23:30:00Z",
                        "AverageListPrice": 0.0,
                        "ListPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 122.4500,
                            "Fuel": {"Percentage": 0.23000, "Amount": 34.200},
                            "TotalSurcharges": 26.250,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 9.143,
                            "Taxes": [
                                {"Name": "GST", "Percentage": 5.0, "Amount": 9.143}
                            ],
                            "Total": 192.043,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.0,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 192.043,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 122.4500,
                                    "Fuel": {"Percentage": 0.23000, "Amount": 34.200},
                                    "TotalSurcharges": 26.250,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 9.143,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 9.143,
                                        }
                                    ],
                                    "Total": 192.043,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.0,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "ClientPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 57.4898000000,
                            "Fuel": {
                                "Percentage": 0.23000,
                                "Amount": 19.260154000000000,
                            },
                            "TotalSurcharges": 26.2498,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 5.149987700000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 5.149987700000000,
                                }
                            ],
                            "Total": 108.149741700000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.00,
                            "TotalPriceInSelectedCurrency": 108.149741700000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 57.4898000000,
                                    "Fuel": {
                                        "Percentage": 0.23000,
                                        "Amount": 19.260154000000000,
                                    },
                                    "TotalSurcharges": 26.2498,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 5.149987700000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 5.149987700000000,
                                        }
                                    ],
                                    "Total": 108.149741700000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.00,
                                }
                            ],
                        },
                        "CustomerPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 57.4898000000,
                            "Fuel": {
                                "Percentage": 0.23000,
                                "Amount": 19.260154000000000,
                            },
                            "TotalSurcharges": 26.2498,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 5.1499877000000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 5.1499877000000000,
                                }
                            ],
                            "Total": 108.1497417000000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 108.1497417000000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 57.4898000000,
                                    "Fuel": {
                                        "Percentage": 0.23000,
                                        "Amount": 19.260154000000000,
                                    },
                                    "TotalSurcharges": 26.2498,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 5.1499877000000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 5.1499877000000000,
                                        }
                                    ],
                                    "Total": 108.1497417000000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "OriginRateZone": "",
                        "DestinationRateZone": "(ALL)",
                    },
                    {
                        "CarrierId": 8,
                        "SCAC": "UPSG",
                        "CarrierName": "UPS",
                        "ERROR": None,
                        "Service": {
                            "Name": "UPS Express Saver®",
                            "Code": "13",
                            "ServiceGroups": [],
                            "DeliveryServiceGroups": None,
                            "GroupsShipmentOptions": None,
                            "PerformanceScore": 0.0,
                            "DeliveryPerformanceOnTimePercentage": 0.0,
                        },
                        "TransitDays": 1,
                        "DeliveryDate": "2023-01-24T23:30:00Z",
                        "AverageListPrice": 0.0,
                        "ListPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 111.8500,
                            "Fuel": {"Percentage": 0.23000, "Amount": 31.770},
                            "TotalSurcharges": 26.250,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 8.502,
                            "Taxes": [
                                {"Name": "GST", "Percentage": 5.0, "Amount": 8.502}
                            ],
                            "Total": 178.372,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.0,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 178.372,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 111.8500,
                                    "Fuel": {"Percentage": 0.23000, "Amount": 31.770},
                                    "TotalSurcharges": 26.250,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 8.502,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 8.502,
                                        }
                                    ],
                                    "Total": 178.372,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.0,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "ClientPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 52.4492000000,
                            "Fuel": {
                                "Percentage": 0.23000,
                                "Amount": 18.100816000000000,
                            },
                            "TotalSurcharges": 26.2502,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 4.840010800000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 4.840010800000000,
                                }
                            ],
                            "Total": 101.640226800000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.00,
                            "TotalPriceInSelectedCurrency": 101.640226800000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 52.4492000000,
                                    "Fuel": {
                                        "Percentage": 0.23000,
                                        "Amount": 18.100816000000000,
                                    },
                                    "TotalSurcharges": 26.2502,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 4.840010800000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 4.840010800000000,
                                        }
                                    ],
                                    "Total": 101.640226800000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.00,
                                }
                            ],
                        },
                        "CustomerPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 52.4492000000,
                            "Fuel": {
                                "Percentage": 0.23000,
                                "Amount": 18.100816000000000,
                            },
                            "TotalSurcharges": 26.2502,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 4.8400108000000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 4.8400108000000000,
                                }
                            ],
                            "Total": 101.6402268000000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 101.6402268000000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 52.4492000000,
                                    "Fuel": {
                                        "Percentage": 0.23000,
                                        "Amount": 18.100816000000000,
                                    },
                                    "TotalSurcharges": 26.2502,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 4.8400108000000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 4.8400108000000000,
                                        }
                                    ],
                                    "Total": 101.6402268000000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "OriginRateZone": "",
                        "DestinationRateZone": "(ALL)",
                    },
                    {
                        "CarrierId": 8,
                        "SCAC": "UPSG",
                        "CarrierName": "UPS",
                        "ERROR": None,
                        "Service": {
                            "Name": "UPS Expedited®",
                            "Code": "02",
                            "ServiceGroups": [],
                            "DeliveryServiceGroups": None,
                            "GroupsShipmentOptions": None,
                            "PerformanceScore": 0.0,
                            "DeliveryPerformanceOnTimePercentage": 0.0,
                        },
                        "TransitDays": 1,
                        "DeliveryDate": "2023-01-24T23:30:00Z",
                        "AverageListPrice": 0.0,
                        "ListPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 107.3500,
                            "Fuel": {"Percentage": 0.23000, "Amount": 30.730},
                            "TotalSurcharges": 26.250,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 8.225,
                            "Taxes": [
                                {"Name": "GST", "Percentage": 5.0, "Amount": 8.225}
                            ],
                            "Total": 172.555,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.0,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 172.555,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 107.3500,
                                    "Fuel": {"Percentage": 0.23000, "Amount": 30.730},
                                    "TotalSurcharges": 26.250,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 8.225,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 8.225,
                                        }
                                    ],
                                    "Total": 172.555,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.0,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "ClientPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 50.2866000000,
                            "Fuel": {
                                "Percentage": 0.23000,
                                "Amount": 17.603418000000000,
                            },
                            "TotalSurcharges": 26.2496,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 4.706980900000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 4.706980900000000,
                                }
                            ],
                            "Total": 98.846598900000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.00,
                            "TotalPriceInSelectedCurrency": 98.846598900000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 50.2866000000,
                                    "Fuel": {
                                        "Percentage": 0.23000,
                                        "Amount": 17.603418000000000,
                                    },
                                    "TotalSurcharges": 26.2496,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 4.706980900000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 4.706980900000000,
                                        }
                                    ],
                                    "Total": 98.846598900000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.00,
                                }
                            ],
                        },
                        "CustomerPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 50.2866000000,
                            "Fuel": {
                                "Percentage": 0.23000,
                                "Amount": 17.603418000000000,
                            },
                            "TotalSurcharges": 26.2496,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 4.7069809000000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 4.7069809000000000,
                                }
                            ],
                            "Total": 98.8465989000000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 98.8465989000000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 50.2866000000,
                                    "Fuel": {
                                        "Percentage": 0.23000,
                                        "Amount": 17.603418000000000,
                                    },
                                    "TotalSurcharges": 26.2496,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 4.7069809000000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 4.7069809000000000,
                                        }
                                    ],
                                    "Total": 98.8465989000000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "OriginRateZone": "",
                        "DestinationRateZone": "(ALL)",
                    },
                    {
                        "CarrierId": 8,
                        "SCAC": "UPSG",
                        "CarrierName": "UPS",
                        "ERROR": None,
                        "Service": {
                            "Name": "UPS Standard®",
                            "Code": "11",
                            "ServiceGroups": [],
                            "DeliveryServiceGroups": None,
                            "GroupsShipmentOptions": None,
                            "PerformanceScore": 0.0,
                            "DeliveryPerformanceOnTimePercentage": 0.0,
                        },
                        "TransitDays": 1,
                        "DeliveryDate": "2023-01-24T23:30:00Z",
                        "AverageListPrice": 0.0,
                        "ListPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 106.4500,
                            "Fuel": {"Percentage": 0.33500, "Amount": 44.450},
                            "TotalSurcharges": 26.250,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 8.863,
                            "Taxes": [
                                {"Name": "GST", "Percentage": 5.0, "Amount": 8.863}
                            ],
                            "Total": 186.013,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.0,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 186.013,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 106.4500,
                                    "Fuel": {"Percentage": 0.33500, "Amount": 44.450},
                                    "TotalSurcharges": 26.250,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 8.863,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 8.863,
                                        }
                                    ],
                                    "Total": 186.013,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.0,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "ClientPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 49.8399000000,
                            "Fuel": {
                                "Percentage": 0.33500,
                                "Amount": 25.490116500000000,
                            },
                            "TotalSurcharges": 26.2499,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 5.078995825000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 5.078995825000000,
                                }
                            ],
                            "Total": 106.658912325000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.00,
                            "TotalPriceInSelectedCurrency": 106.658912325000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 49.8399000000,
                                    "Fuel": {
                                        "Percentage": 0.33500,
                                        "Amount": 25.490116500000000,
                                    },
                                    "TotalSurcharges": 26.2499,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 5.078995825000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 5.078995825000000,
                                        }
                                    ],
                                    "Total": 106.658912325000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.00,
                                }
                            ],
                        },
                        "CustomerPrice": {
                            "DimensionalWeight": 0.0,
                            "BilledWeight": 30.0,
                            "WeightType": 1,
                            "Freight": 49.8399000000,
                            "Fuel": {
                                "Percentage": 0.33500,
                                "Amount": 25.490116500000000,
                            },
                            "TotalSurcharges": 26.2499,
                            "Surcharges": [
                                {
                                    "Code": None,
                                    "Name": "Additional Handling",
                                    "AffectsFuel": False,
                                    "Amount": 26.25,
                                }
                            ],
                            "TotalTaxes": 5.0789958250000000,
                            "Taxes": [
                                {
                                    "Name": "GST",
                                    "Percentage": 5.0,
                                    "Amount": 5.0789958250000000,
                                }
                            ],
                            "Total": 106.6589123250000000,
                            "Currency": "CAD",
                            "OnlinePaymentFee": 0.00,
                            "TransactionFee": 0.0,
                            "PickupFee": 0.0,
                            "TotalPriceInSelectedCurrency": 106.6589123250000000,
                            "PackagePrices": [
                                {
                                    "DimensionalWeight": 0.0,
                                    "BilledWeight": 30.0,
                                    "WeightType": 1,
                                    "Freight": 49.8399000000,
                                    "Fuel": {
                                        "Percentage": 0.33500,
                                        "Amount": 25.490116500000000,
                                    },
                                    "TotalSurcharges": 26.2499,
                                    "Surcharges": [
                                        {
                                            "Code": None,
                                            "Name": "Additional Handling",
                                            "AffectsFuel": False,
                                            "Amount": 26.25,
                                        }
                                    ],
                                    "TotalTaxes": 5.0789958250000000,
                                    "Taxes": [
                                        {
                                            "Name": "GST",
                                            "Percentage": 5.0,
                                            "Amount": 5.0789958250000000,
                                        }
                                    ],
                                    "Total": 106.6589123250000000,
                                    "Currency": "CAD",
                                    "OnlinePaymentFee": 0.00,
                                    "TransactionFee": 0.0,
                                    "PickupFee": 0.0,
                                }
                            ],
                        },
                        "OriginRateZone": "",
                        "DestinationRateZone": "(ALL)",
                    },
                ],
                "ExchangeRate": {
                    "Value": 1.0,
                    "FromCurrency": "CAD",
                    "ToCurrency": "CAD",
                },
                "DutiesAndTaxesCost": None,
                "RatedPackages": None,
            }
        ]

        self._two_rate = TwoShipRate(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test TwoShip rate address building for origin
        :return:
        """

        ret = self._two_rate._build_address(
            address=self.request["origin"], carrier_id=UPS
        )
        expected = {
            "Address1": "1540 Airport Road",
            "City": "edmonton international airport",
            "CompanyName": "BBE Ottawa",
            "Country": "CA",
            "IsResidential": False,
            "PostalCode": "T9E0V6",
            "State": "AB",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test TwoShip rate address building for destination
        :return:
        """

        ret = self._two_rate._build_address(
            address=self.request["destination"], carrier_id=UPS
        )
        expected = {
            "Address1": "140 THAD JOHNSON PRIV Suite 7",
            "City": "ottawa",
            "CompanyName": "BBE Ottawa",
            "Country": "CA",
            "IsResidential": False,
            "PostalCode": "K1V0R1",
            "State": "ON",
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages(self):
        """
        Test TwoShip rate package building
        :return:
        """

        ret = self._two_rate._build_packages()
        expected = [
            {
                "DimensionType": 1,
                "WeightType": 1,
                "Length": Decimal("48.00"),
                "Width": Decimal("48.00"),
                "Height": Decimal("48.00"),
                "Weight": Decimal("100.00"),
            }
        ]
        self.assertListEqual(expected, ret)

    def test_build_packages_quantity(self):
        """
        Test TwoShip rate package building
        :return:
        """
        copied = copy.deepcopy(self.request)
        copied["packages"][0]["quantity"] = 5

        ret = TwoShipRate(ubbe_request=copied)._build_packages()
        expected = [
            {
                "DimensionType": 1,
                "WeightType": 1,
                "Length": Decimal("48.00"),
                "Width": Decimal("48.00"),
                "Height": Decimal("48.00"),
                "Weight": Decimal("100.00"),
            },
            {
                "DimensionType": 1,
                "WeightType": 1,
                "Length": Decimal("48.00"),
                "Width": Decimal("48.00"),
                "Height": Decimal("48.00"),
                "Weight": Decimal("100.00"),
            },
            {
                "DimensionType": 1,
                "WeightType": 1,
                "Length": Decimal("48.00"),
                "Width": Decimal("48.00"),
                "Height": Decimal("48.00"),
                "Weight": Decimal("100.00"),
            },
            {
                "DimensionType": 1,
                "WeightType": 1,
                "Length": Decimal("48.00"),
                "Width": Decimal("48.00"),
                "Height": Decimal("48.00"),
                "Weight": Decimal("100.00"),
            },
            {
                "DimensionType": 1,
                "WeightType": 1,
                "Length": Decimal("48.00"),
                "Width": Decimal("48.00"),
                "Height": Decimal("48.00"),
                "Weight": Decimal("100.00"),
            },
        ]
        self.assertListEqual(expected, ret)

    def test_build(self):
        """
        Test TwoShip rate package building
        :return:
        """

        self._two_rate._build()
        expected = [
            {
                "LocationId": 4110,
                "CarrierID": 8,
                "Sender": {
                    "Address1": "1540 Airport Road",
                    "City": "edmonton international airport",
                    "CompanyName": "BBE Ottawa",
                    "Country": "CA",
                    "IsResidential": False,
                    "PostalCode": "T9E0V6",
                    "State": "AB",
                },
                "Recipient": {
                    "Address1": "140 THAD JOHNSON PRIV Suite 7",
                    "City": "ottawa",
                    "CompanyName": "BBE Ottawa",
                    "Country": "CA",
                    "IsResidential": False,
                    "PostalCode": "K1V0R1",
                    "State": "ON",
                },
                "Packages": [
                    {
                        "DimensionType": 1,
                        "WeightType": 1,
                        "Length": Decimal("48.00"),
                        "Width": Decimal("48.00"),
                        "Height": Decimal("48.00"),
                        "Weight": Decimal("100.00"),
                    }
                ],
                "ShipmentOptions": {"SignatureRequired": True},
                "PickupRequest": True,
                "InternationalOptions": {"Invoice": {"Currency": "CAD"}},
            }
        ]

        for r in self._two_rate._requests:
            del r["WS_Key"]

        self.assertListEqual(expected, self._two_rate._requests)

    def test_format_response(self):
        """
        Test TwoShip rate package building
        :return:
        """

        self._two_rate._responses = self._two_response
        rates = self._two_rate._format_response()
        expected = [
            {
                "carrier_id": 8,
                "carrier_name": "UPS",
                "service_code": "01",
                "service_name": "UPS Express®",
                "freight": Decimal("57.49"),
                "surcharge": Decimal("45.51"),
                "tax": Decimal("5.15"),
                "tax_percent": Decimal("5.00"),
                "total": Decimal("108.15"),
                "transit_days": 1,
                "delivery_date": "2023-01-24T23:30:00Z",
            },
            {
                "carrier_id": 8,
                "carrier_name": "UPS",
                "service_code": "13",
                "service_name": "UPS Express Saver®",
                "freight": Decimal("52.45"),
                "surcharge": Decimal("44.35"),
                "tax": Decimal("4.84"),
                "tax_percent": Decimal("5.00"),
                "total": Decimal("101.64"),
                "transit_days": 1,
                "delivery_date": "2023-01-24T23:30:00Z",
            },
            {
                "carrier_id": 8,
                "carrier_name": "UPS",
                "service_code": "02",
                "service_name": "UPS Expedited®",
                "freight": Decimal("50.29"),
                "surcharge": Decimal("43.85"),
                "tax": Decimal("4.71"),
                "tax_percent": Decimal("5.00"),
                "total": Decimal("98.85"),
                "transit_days": 1,
                "delivery_date": "2023-01-24T23:30:00Z",
            },
            {
                "carrier_id": 8,
                "carrier_name": "UPS",
                "service_code": "11",
                "service_name": "UPS Standard®",
                "freight": Decimal("49.84"),
                "surcharge": Decimal("51.74"),
                "tax": Decimal("5.08"),
                "tax_percent": Decimal("5.00"),
                "total": Decimal("106.66"),
                "transit_days": 1,
                "delivery_date": "2023-01-24T23:30:00Z",
            },
        ]
        self.assertListEqual(expected, rates)
