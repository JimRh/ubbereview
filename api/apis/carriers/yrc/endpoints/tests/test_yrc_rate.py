"""
    Title: YRC Rate Unit Tests
    Description: Unit Tests for the YRC Rate. Test Everything.
    Created: January 18, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.yrc.endpoints.yrc_rate import YRCRate
from api.exceptions.project import RateException
from api.globals.carriers import YRC
from api.models import SubAccount, Carrier, CarrierAccount


class YRCRateTests(TestCase):
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
        carrier = Carrier.objects.get(code=YRC)
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
                "is_residential": False,
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "city": "Ottawa",
                "company_name": "BBE Ottawa",
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
                }
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    YRC: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
        }

        self.response_good = {
            "isSuccess": True,
            "errors": [],
            "warnings": None,
            "pageRoot": {
                "context": "my.yrc.com",
                "programId": "TFQ622",
                "queryType": "RateQuote",
                "dateTime": "2022041915142530",
                "returnCode": "0000",
                "returnText": "QuerySuccessful",
                "recordCount": "0",
                "recordOffset": "0",
                "maxRecords": "0",
                "pageHead": {"pageTitle": "YRC", "pageSubTitle": "RateQuote"},
                "bodyHead": {
                    "bodyTitle": "QuoteServiceComputeResults",
                    "message": "Computesuccessful",
                },
                "bodyMain": {
                    "rateQuote": {
                        "referenceId": "2CAR22109345247F5197",
                        "quoteId": "25111287",
                        "paymentTerms": "Prepaid",
                        "payerRole": "ThirdParty",
                        "pickupDate": 20220419,
                        "delivery": {
                            "requestedServiceType": {"value": "Standard"},
                            "requestedDateTime": {"requestedTime": [{"type": "End"}]},
                            "standardDate": 20220426,
                            "standardDays": 5,
                        },
                        "currency": "CAD",
                        "location": [
                            {
                                "role": "Origin",
                                "city": "TAMPA",
                                "statePostalCode": "FL",
                                "zipCode": "33602",
                                "nationCode": "USA",
                                "terminal": 754,
                                "zone": "1",
                                "typeService": "Direct",
                            },
                            {
                                "role": "Destination",
                                "city": "EDMONTONINTLAIRPORT",
                                "statePostalCode": "AB",
                                "zipCode": "T9E0V6",
                                "nationCode": "CAN",
                                "terminal": 627,
                                "zone": "2",
                                "typeService": "Direct",
                            },
                        ],
                        "customer": [
                            {
                                "role": "Shipper",
                                "city": "TAMPA",
                                "statePostalCode": "FL",
                                "zipCode": "33602",
                                "nationCode": "USA",
                            },
                            {
                                "role": "Consignee",
                                "city": "EDMONTONINTLAIRPORT",
                                "statePostalCode": "AB",
                                "zipCode": "T9E0V6",
                                "nationCode": "CAN",
                            },
                            {
                                "role": "ThirdParty",
                                "name": "BRADENBURRYEXPEDITING",
                                "address": "175935AVEE",
                                "city": "EDMONTON",
                                "statePostalCode": "AB",
                                "zipCode": "T9E0V6",
                                "nationCode": "CAN",
                                "terminal": "627",
                                "account": "9594",
                                "busId": "12250593508",
                                "locationCreditIndicator": "Y",
                            },
                        ],
                        "lineItem": [
                            {
                                "type": "Commodity",
                                "handlingUnits": {
                                    "count": 4,
                                    "packageCode": "SKD",
                                    "length": 48,
                                    "width": 48,
                                    "height": 48,
                                },
                                "pieces": {},
                                "hazardous": "N",
                                "nmfc": {"class": "50"},
                                "weight": 500,
                                "density": "1.95",
                                "ratedType": "E",
                                "ratedClass": "E300",
                                "ratedWeight": 500,
                                "rate": "212775",
                                "rateUOM": "LBS",
                                "charges": "1380803",
                                "weightUOM": "LB",
                                "ratePerUOM": "CWT",
                            },
                            {
                                "type": "CodeWord",
                                "description": "PERCENTDISCOUNT",
                                "code": "DISC",
                                "rate": "92.40",
                                "charges": "1275862",
                                "terms": "P",
                                "creditInd": "-",
                                "disposition": "2",
                                "sourceCode": "R",
                            },
                            {
                                "type": "CodeWord",
                                "description": "GENERALSURCHARGE(FUEL/FRT)",
                                "code": "FSC",
                                "rate": "4360",
                                "rateUOM": "%",
                                "charges": "45753",
                                "terms": "P",
                                "ratePerUOM": "NRVA",
                                "creditInd": "+",
                                "disposition": "2",
                                "sourceCode": "B",
                            },
                            {
                                "type": "CodeWord",
                                "description": "CANADIANPROCESSINGCHARGE",
                                "code": "CNSC",
                                "rateUOM": "$",
                                "charges": "4542",
                                "terms": "P",
                                "ratePerUOM": "SHPT",
                                "creditInd": "+",
                                "disposition": "2",
                                "sourceCode": "B",
                            },
                            {
                                "type": "CodeWord",
                                "description": "TOTAL/SUBTOTALBILLEDCHARGES",
                                "code": "TTL",
                                "quantity": "500",
                                "charges": "155236",
                                "terms": "P",
                                "creditInd": "+",
                                "disposition": "2",
                                "sourceCode": "R",
                            },
                        ],
                        "vendorSCAC": "RDWY",
                        "publishRateFlag": "N",
                        "minCharge": "17000",
                        "guaranteeFlag": "N",
                        "ratedCharges": {
                            "freightCharges": 104940,
                            "otherCharges": 50296,
                            "totalCharges": 155236,
                        },
                        "shipmentRateUnit": "CWT",
                        "shipmentPricePerUnit": 21277500,
                        "pricing": [
                            {
                                "agent": "RDWY",
                                "tariff": "8C799",
                                "item": "5432",
                                "applyPayTerms": "P",
                                "usedFlag": "Y",
                                "role": "T",
                                "pricingType": "C",
                                "type": "L",
                            },
                            {
                                "agent": "RDWY",
                                "tariff": "8C799",
                                "item": "5103",
                                "applyPayTerms": "P",
                                "usedFlag": "Y",
                                "role": "T",
                                "pricingType": "C",
                                "type": "T",
                            },
                            {
                                "agent": "YRC",
                                "tariff": "551",
                                "item": "3010",
                                "type": "B",
                            },
                        ],
                        "promoCodeInfo": {},
                        "liability": {},
                        "dimFactor": "ACT",
                        "ratedPricingDays": "0",
                        "accSrvcCount": "4",
                        "commodityCount": "1",
                        "minChargeFloor": "17000",
                        "weight": 500,
                        "ratedWeight": 500,
                        "quoteType": "QUOTE",
                        "linearFeet": "8",
                        "cubicFeet": "256",
                        "calcCubicFeet": "256",
                        "fullVisibleCapacity": "12",
                        "positionHours": "6",
                    }
                },
            },
        }
        self.response_error = {
            "isSuccess": False,
            "errors": [
                {"field": "0050", "message": "Invalid destination city/state/zip."}
            ],
            "warnings": None,
            "pageRoot": None,
        }
        self._yrc_rate = YRCRate(ubbe_request=self.request)

    def test_build_packages(self):
        """
        Test Rate Building of packages.
        """
        ret = self._yrc_rate._build_packages(packages=self.request["packages"])
        expected = {
            "commodity": [
                {
                    "packageCode": "SKD",
                    "nmfcClass": 70,
                    "handlingUnits": 1,
                    "packageLength": Decimal("48"),
                    "packageWidth": Decimal("48"),
                    "packageHeight": Decimal("48"),
                    "weight": Decimal("100"),
                }
            ]
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages_with_drum(self):
        """
        Test Rate Building with multiple packages.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
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
            }
        )

        ret = self._yrc_rate._build_packages(packages=copied["packages"])
        expected = {
            "commodity": [
                {
                    "packageCode": "SKD",
                    "nmfcClass": 70,
                    "handlingUnits": 1,
                    "packageLength": Decimal("48"),
                    "packageWidth": Decimal("48"),
                    "packageHeight": Decimal("48"),
                    "weight": Decimal("100"),
                },
                {
                    "packageCode": "DRM",
                    "nmfcClass": 70,
                    "handlingUnits": 1,
                    "packageLength": Decimal("48"),
                    "packageWidth": Decimal("48"),
                    "packageHeight": Decimal("48"),
                    "weight": Decimal("100"),
                },
            ]
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_origin(self):
        """
        Test Rate Building of origin address.
        """
        ret = self._yrc_rate._build_address(address=self.request["origin"])
        expected = {
            "city": "edmonton international airport",
            "state": "AB",
            "postalCode": "T9E0V6",
            "country": "CAN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test Rate Building of destination address.
        """
        ret = self._yrc_rate._build_address(address=self.request["destination"])
        expected = {
            "city": "ottawa",
            "state": "ON",
            "postalCode": "K1V0R1",
            "country": "CAN",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_usa(self):
        """
        Test Rate Building of destination address.
        """
        copied = copy.deepcopy(self.request)
        copied["origin"] = {
            "address": "452 Morse Road",
            "city": "Bennington",
            "company_name": "BBE Ottawa",
            "country": "US",
            "postal_code": "05201",
            "province": "VT",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = self._yrc_rate._build_address(address=copied["origin"])
        expected = {
            "city": "bennington",
            "state": "VT",
            "postalCode": "05201",
            "country": "USA",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_mexico(self):
        """
        Test Rate Building of destination address.
        """
        copied = copy.deepcopy(self.request)
        copied["origin"] = {
            "address": "Predio Paraiso Escondido s/n",
            "city": "Cabo San Lucas",
            "company_name": "BBE Ottawa",
            "country": "MX",
            "postal_code": "23450",
            "province": "BCS",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = self._yrc_rate._build_address(address=copied["origin"])
        expected = {
            "city": "cabo san lucas",
            "state": "BCS",
            "postalCode": "23450",
            "country": "MEX",
        }
        self.assertDictEqual(expected, ret)

    def test_build_options_inside_pickup(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(9)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": ["IP"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_inside_delivery(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(10)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": ["ID"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_power_tailgate_pickup(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(3)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": ["LFTO"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_power_tailgate_delivery(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(17)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": ["LFTD"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_delivery_appointment(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(1)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": ["APPT"]}
        self.assertDictEqual(expected, ret)

    # def test_build_options_heated_truck(self):
    #     """
    #         Test Rate Building of carrier options that ubbe supports
    #     """
    #     copied = copy.deepcopy(self.request)
    #     copied["carrier_options"].append(6)
    #
    #     ret = self._yrc_rate._build_options(options=copied["carrier_options"])
    #     expected = {'accOptions': ['FREZ']}
    #     self.assertDictEqual(expected, ret)

    def test_build_options_origin_is_residential(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["origin"]["has_shipping_bays"] = False

        ret = YRCRate(ubbe_request=copied)._build_options(
            options=copied["carrier_options"]
        )
        expected = {"accOptions": ["HOMP"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_destination_is_residential(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["destination"]["has_shipping_bays"] = False

        ret = YRCRate(ubbe_request=copied)._build_options(
            options=copied["carrier_options"]
        )
        expected = {"accOptions": ["HOMD"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_multiple(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(17)
        copied["carrier_options"].append(1)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": ["LFTD", "APPT"]}
        self.assertDictEqual(expected, ret)

    def test_build_options_no_options(self):
        """
        Test Rate Building of carrier options that ubbe supports
        """
        copied = copy.deepcopy(self.request)

        ret = self._yrc_rate._build_options(options=copied["carrier_options"])
        expected = {"accOptions": []}
        self.assertDictEqual(expected, ret)

    def test_create_request(self):
        """
        Test Rate Building whole request.
        """
        ret = self._yrc_rate._create_request()
        expected = {
            "login": {
                "username": "BBEYZF",
                "password": "BBEYZF",
                "busId": "BBEYZF",
                "busRole": "Third Party",
                "paymentTerms": "Prepaid",
            },
            "originLocation": {
                "city": "edmonton international airport",
                "state": "AB",
                "postalCode": "T9E0V6",
                "country": "CAN",
            },
            "destinationLocation": {
                "city": "ottawa",
                "state": "ON",
                "postalCode": "K1V0R1",
                "country": "CAN",
            },
            "details": {
                "serviceClass": "STD",
                "typeQuery": "QUOTE",
                "currency": "CAD",
                "acceptTerms": True,
            },
            "listOfCommodities": {
                "commodity": [
                    {
                        "packageCode": "SKD",
                        "nmfcClass": 70,
                        "handlingUnits": 1,
                        "packageLength": 48,
                        "packageWidth": 48,
                        "packageHeight": 48,
                        "weight": 100,
                    }
                ]
            },
            "serviceOpts": {"accOptions": []},
        }
        del ret["details"]["pickupDate"]
        self.assertDictEqual(expected, ret)

    def test_create_request_multiple_package(self):
        """
        Test Rate Building whole request with multiple packages
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
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
            }
        )

        ret = YRCRate(ubbe_request=copied)._create_request()
        expected = {
            "login": {
                "username": "BBEYZF",
                "password": "BBEYZF",
                "busId": "BBEYZF",
                "busRole": "Third Party",
                "paymentTerms": "Prepaid",
            },
            "originLocation": {
                "city": "edmonton international airport",
                "state": "AB",
                "postalCode": "T9E0V6",
                "country": "CAN",
            },
            "destinationLocation": {
                "city": "ottawa",
                "state": "ON",
                "postalCode": "K1V0R1",
                "country": "CAN",
            },
            "details": {
                "serviceClass": "STD",
                "typeQuery": "QUOTE",
                "currency": "CAD",
                "acceptTerms": True,
            },
            "listOfCommodities": {
                "commodity": [
                    {
                        "packageCode": "SKD",
                        "nmfcClass": 70,
                        "handlingUnits": 1,
                        "packageLength": 48,
                        "packageWidth": 48,
                        "packageHeight": 48,
                        "weight": 100,
                    },
                    {
                        "packageCode": "DRM",
                        "nmfcClass": 70,
                        "handlingUnits": 1,
                        "packageLength": 48,
                        "packageWidth": 48,
                        "packageHeight": 48,
                        "weight": 100,
                    },
                ]
            },
            "serviceOpts": {"accOptions": []},
        }
        del ret["details"]["pickupDate"]
        self.assertDictEqual(expected, ret)

    def test_create_request_multiple_options(self):
        """
        Test Rate Building whole request with multiple options
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].append(17)
        copied["carrier_options"].append(1)

        ret = YRCRate(ubbe_request=copied)._create_request()
        expected = {
            "login": {
                "username": "BBEYZF",
                "password": "BBEYZF",
                "busId": "BBEYZF",
                "busRole": "Third Party",
                "paymentTerms": "Prepaid",
            },
            "originLocation": {
                "city": "edmonton international airport",
                "state": "AB",
                "postalCode": "T9E0V6",
                "country": "CAN",
            },
            "destinationLocation": {
                "city": "ottawa",
                "state": "ON",
                "postalCode": "K1V0R1",
                "country": "CAN",
            },
            "details": {
                "serviceClass": "STD",
                "typeQuery": "QUOTE",
                "currency": "CAD",
                "acceptTerms": True,
            },
            "listOfCommodities": {
                "commodity": [
                    {
                        "packageCode": "SKD",
                        "nmfcClass": 70,
                        "handlingUnits": 1,
                        "packageLength": 48,
                        "packageWidth": 48,
                        "packageHeight": 48,
                        "weight": 100,
                    }
                ]
            },
            "serviceOpts": {"accOptions": ["LFTD", "APPT"]},
        }
        del ret["details"]["pickupDate"]
        self.assertDictEqual(expected, ret)

    def test_create_request_usa(self):
        """
        Test Rate Building whole request with US origin
        """
        copied = copy.deepcopy(self.request)
        copied["origin"] = {
            "address": "452 Morse Road",
            "city": "Bennington",
            "company_name": "BBE Ottawa",
            "country": "US",
            "postal_code": "05201",
            "province": "VT",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = YRCRate(ubbe_request=copied)._create_request()
        expected = {
            "login": {
                "username": "BBEYZF",
                "password": "BBEYZF",
                "busId": "BBEYZF",
                "busRole": "Third Party",
                "paymentTerms": "Prepaid",
            },
            "originLocation": {
                "city": "bennington",
                "state": "VT",
                "postalCode": "05201",
                "country": "USA",
            },
            "destinationLocation": {
                "city": "ottawa",
                "state": "ON",
                "postalCode": "K1V0R1",
                "country": "CAN",
            },
            "details": {
                "serviceClass": "STD",
                "typeQuery": "QUOTE",
                "currency": "CAD",
                "acceptTerms": True,
            },
            "listOfCommodities": {
                "commodity": [
                    {
                        "packageCode": "SKD",
                        "nmfcClass": 70,
                        "handlingUnits": 1,
                        "packageLength": 48,
                        "packageWidth": 48,
                        "packageHeight": 48,
                        "weight": 100,
                    }
                ]
            },
            "serviceOpts": {"accOptions": []},
        }
        del ret["details"]["pickupDate"]
        self.assertDictEqual(expected, ret)

    def test_create_request_mexico(self):
        """
        Test Rate Building whole request with MX origin
        """
        copied = copy.deepcopy(self.request)
        copied["origin"] = {
            "address": "Predio Paraiso Escondido s/n",
            "city": "Cabo San Lucas",
            "company_name": "BBE Ottawa",
            "country": "MX",
            "postal_code": "23450",
            "province": "BCS",
            "is_residential": False,
            "has_shipping_bays": True,
        }

        ret = YRCRate(ubbe_request=copied)._create_request()
        expected = {
            "login": {
                "username": "BBEYZF",
                "password": "BBEYZF",
                "busId": "BBEYZF",
                "busRole": "Third Party",
                "paymentTerms": "Prepaid",
            },
            "originLocation": {
                "city": "cabo san lucas",
                "state": "BCS",
                "postalCode": "23450",
                "country": "MEX",
            },
            "destinationLocation": {
                "city": "ottawa",
                "state": "ON",
                "postalCode": "K1V0R1",
                "country": "CAN",
            },
            "details": {
                "serviceClass": "STD",
                "typeQuery": "QUOTE",
                "currency": "CAD",
                "acceptTerms": True,
            },
            "listOfCommodities": {
                "commodity": [
                    {
                        "packageCode": "SKD",
                        "nmfcClass": 70,
                        "handlingUnits": 1,
                        "packageLength": 48,
                        "packageWidth": 48,
                        "packageHeight": 48,
                        "weight": 100,
                    }
                ]
            },
            "serviceOpts": {"accOptions": []},
        }
        del ret["details"]["pickupDate"]
        self.assertDictEqual(expected, ret)

    def test_format_response(self):
        """
        Test Rate response formatting raates
        """

        ret = self._yrc_rate._format_response(
            response=self.response_good, service_code="ST"
        )
        expected = {
            "carrier_id": 523,
            "carrier_name": "YRC Freight",
            "service_code": "ST|25111287",
            "service_name": "Standard",
            "freight": Decimal("1049.40"),
            "surcharge": Decimal("502.96"),
            "tax": Decimal("0.00"),
            "tax_percent": Decimal("0.00"),
            "total": Decimal("1552.36"),
            "transit_days": 5,
            "delivery_date": "2022-04-26T00:00:00",
        }
        self.assertDictEqual(expected, ret)

    def test_format_response_no_rates(self):
        """
        Test Rate response formatting no rates
        """

        with self.assertRaises(RateException) as context:
            self._yrc_rate._format_response(
                response=self.response_error, service_code="A"
            )
