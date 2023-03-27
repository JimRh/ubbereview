"""
    Title: Purolator Rate Unit Tests
    Description: Unit Tests for the Purolator Rate. Test Everything.
    Created: November 25, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.purolator.courier.endpoints.purolator_rate import PurolatorRate
from api.models import SubAccount, Carrier, CarrierAccount


class PurolatorRateTests(TestCase):
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
            "pickup": {
                "date": "2021-08-12",
                "start_time": "10:00",
                "end_time": "16:00",
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
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    11: {"account": carrier_account, "carrier": carrier}
                },
            },
        }

        self.response = [
            {
                "ServiceID": "PurolatorExpress9AM",
                "ShipmentDate": "2020-12-04",
                "ExpectedDeliveryDate": "2020-12-07",
                "EstimatedTransitDays": 1,
                "BasePrice": Decimal("132.35"),
                "Surcharges": {
                    "Surcharge": [
                        {
                            "Amount": Decimal("2.95"),
                            "Type": "ResidentialDelivery",
                            "Description": "Residential Area",
                        },
                        {
                            "Amount": Decimal("22.24"),
                            "Type": "Fuel",
                            "Description": "Fuel",
                        },
                    ]
                },
                "Taxes": {
                    "Tax": [
                        {
                            "Amount": Decimal("0"),
                            "Type": "PSTQST",
                            "Description": "PST/QST",
                        },
                        {"Amount": Decimal("0"), "Type": "HST", "Description": "HST"},
                        {
                            "Amount": Decimal("10.38"),
                            "Type": "GST",
                            "Description": "GST",
                        },
                    ]
                },
                "OptionPrices": {
                    "OptionPrice": [
                        {
                            "Amount": Decimal("50"),
                            "ID": "ResidentialAreaHeavyweight",
                            "Description": "Special Handling - Residential Area Heavy Weight(1pc)",
                        }
                    ]
                },
                "TotalPrice": Decimal("217.92"),
            },
            {
                "ServiceID": "PurolatorExpress12PM",
                "ShipmentDate": "2020-12-04",
                "ExpectedDeliveryDate": "2020-12-07",
                "EstimatedTransitDays": 1,
                "BasePrice": Decimal("65.85"),
                "Surcharges": {
                    "Surcharge": [
                        {
                            "Amount": Decimal("2.95"),
                            "Type": "ResidentialDelivery",
                            "Description": "Residential Area",
                        },
                        {
                            "Amount": Decimal("14.26"),
                            "Type": "Fuel",
                            "Description": "Fuel",
                        },
                    ]
                },
                "Taxes": {
                    "Tax": [
                        {
                            "Amount": Decimal("0"),
                            "Type": "PSTQST",
                            "Description": "PST/QST",
                        },
                        {"Amount": Decimal("0"), "Type": "HST", "Description": "HST"},
                        {
                            "Amount": Decimal("6.65"),
                            "Type": "GST",
                            "Description": "GST",
                        },
                    ]
                },
                "OptionPrices": {
                    "OptionPrice": [
                        {
                            "Amount": Decimal("50"),
                            "ID": "ResidentialAreaHeavyweight",
                            "Description": "Special Handling - Residential Area Heavy Weight(1pc)",
                        }
                    ]
                },
                "TotalPrice": Decimal("139.71"),
            },
        ]

        self._puro_rate = PurolatorRate(ubbe_request=self.request)

    def test_get_tax_gst(self):
        data = [
            {"Amount": Decimal("0"), "Type": "PSTQST", "Description": "PST/QST"},
            {"Amount": Decimal("0"), "Type": "HST", "Description": "HST"},
            {"Amount": Decimal("6.65"), "Type": "GST", "Description": "GST"},
        ]

        tax = self._puro_rate._get_tax(taxes=data, total=Decimal("139.71"))
        expected = {"tax": Decimal("6.65"), "tax_percent": Decimal("5")}
        self.assertDictEqual(expected, tax)

    def test_get_tax_hst(self):
        data = [
            {"Amount": Decimal("0"), "Type": "PSTQST", "Description": "PST/QST"},
            {"Amount": Decimal("12.65"), "Type": "HST", "Description": "HST"},
            {"Amount": Decimal("0"), "Type": "GST", "Description": "GST"},
        ]

        tax = self._puro_rate._get_tax(taxes=data, total=Decimal("139.71"))
        expected = {"tax": Decimal("12.65"), "tax_percent": Decimal("10")}
        self.assertDictEqual(expected, tax)

    def test_get_tax_pst(self):
        data = [
            {"Amount": Decimal("18.65"), "Type": "PSTQST", "Description": "PST/QST"},
            {"Amount": Decimal("0"), "Type": "HST", "Description": "HST"},
            {"Amount": Decimal("0"), "Type": "GST", "Description": "GST"},
        ]

        tax = self._puro_rate._get_tax(taxes=data, total=Decimal("139.71"))
        expected = {"tax": Decimal("18.65"), "tax_percent": Decimal("15")}
        self.assertDictEqual(expected, tax)

    def test_get_surcharges(self):
        data = [
            {
                "Amount": Decimal("2.95"),
                "Type": "ResidentialDelivery",
                "Description": "Residential Area",
            },
            {"Amount": Decimal("14.26"), "Type": "Fuel", "Description": "Fuel"},
        ]

        tax = self._puro_rate._get_surcharges(surcharges=data)
        expected = Decimal("17.21")
        self.assertEqual(expected, tax)

    def test_get_surcharges_list(self):
        data = [
            {
                "Amount": Decimal("2.95"),
                "Type": "ResidentialDelivery",
                "Description": "Residential Area",
            },
            {"Amount": Decimal("14.26"), "Type": "Fuel", "Description": "Fuel"},
        ]

        s_list, cost = self._puro_rate._get_surcharges_list(surcharges=data)
        expected = Decimal("17.21")
        expected_list = [
            {
                "name": "Residential Area",
                "cost": Decimal("2.95"),
                "percentage": Decimal("0"),
            },
            {"name": "Fuel", "cost": Decimal("14.26"), "percentage": Decimal("0")},
        ]

        self.assertEqual(expected, cost)
        self.assertIsInstance(s_list, list)
        self.assertEqual(expected_list, s_list)

    def test_get_option_prices(self):
        data = [
            {
                "Amount": Decimal("50"),
                "ID": "ResidentialAreaHeavyweight",
                "Description": "Special Handling - Residential Area Heavy Weight(1pc)",
            }
        ]

        tax = self._puro_rate._get_option_prices(options=data)
        expected = Decimal("50")
        self.assertEqual(expected, tax)

    def test_get_option_prices_list(self):
        data = [
            {
                "Amount": Decimal("50"),
                "ID": "ResidentialAreaHeavyweight",
                "Description": "Special Handling - Residential Area Heavy Weight(1pc)",
            }
        ]

        o_list, cost = self._puro_rate._get_option_prices_list(options=data)
        expected = Decimal("50")
        expected_list = [
            {
                "name": "Special Handling - Residential Area Heavy Weight(1pc)",
                "cost": Decimal("50"),
                "percentage": Decimal("0"),
            }
        ]
        self.assertEqual(expected, cost)
        self.assertIsInstance(o_list, list)
        self.assertEqual(expected_list, o_list)

    def test_format_response(self):
        self._puro_rate.format_response(rates=self.response)
        expected = [
            {
                "carrier_id": 11,
                "carrier_name": "Purolator",
                "service_code": "PurolatorExpress9AM",
                "service_name": "Purolator Express® 9AM",
                "freight": Decimal("132.35"),
                "surcharge": Decimal("75.19"),
                "total": Decimal("217.92"),
                "transit_days": 1,
                "delivery_date": "2020-12-07T00:00:00",
                "origin": "Edmonton International Airport",
                "destination": "Edmonton",
                "tax": Decimal("10.38"),
                "tax_percent": Decimal("5"),
            },
            {
                "carrier_id": 11,
                "carrier_name": "Purolator",
                "service_code": "PurolatorExpress12PM",
                "service_name": "Purolator Express® 12PM",
                "freight": Decimal("65.85"),
                "surcharge": Decimal("67.21"),
                "total": Decimal("139.71"),
                "transit_days": 1,
                "delivery_date": "2020-12-07T00:00:00",
                "origin": "Edmonton International Airport",
                "destination": "Edmonton",
                "tax": Decimal("6.65"),
                "tax_percent": Decimal("5"),
            },
        ]
        self.assertEqual(expected, self._puro_rate._response)

    def test_format_response_two(self):
        copied = copy.deepcopy(self.response)
        copied.pop()
        self._puro_rate.format_response(rates=copied)
        expected = [
            {
                "carrier_id": 11,
                "carrier_name": "Purolator",
                "service_code": "PurolatorExpress9AM",
                "service_name": "Purolator Express® 9AM",
                "freight": Decimal("132.35"),
                "surcharge": Decimal("75.19"),
                "total": Decimal("217.92"),
                "transit_days": 1,
                "delivery_date": "2020-12-07T00:00:00",
                "origin": "Edmonton International Airport",
                "destination": "Edmonton",
                "tax": Decimal("10.38"),
                "tax_percent": Decimal("5"),
            }
        ]
        self.assertEqual(expected, self._puro_rate._response)

    def test_format_response_single(self):
        copied = copy.deepcopy(self.response)
        copied.pop()
        ret = self._puro_rate.format_response_single(rates=copied)
        expected = {
            "freight": Decimal("132.35"),
            "surcharges": [
                {
                    "name": "Residential Area",
                    "cost": Decimal("2.95"),
                    "percentage": Decimal("0"),
                },
                {"name": "Fuel", "cost": Decimal("22.24"), "percentage": Decimal("0")},
                {
                    "name": "Special Handling - Residential Area Heavy Weight(1pc)",
                    "cost": Decimal("50"),
                    "percentage": Decimal("0"),
                },
            ],
            "surcharge": Decimal("75.19"),
            "tax": Decimal("10.38"),
            "tax_percent": Decimal("5"),
            "total": Decimal("217.92"),
            "transit_days": 1,
            "delivery_date": "2020-12-07T00:00:00",
        }
        self.assertDictEqual(expected, ret)
