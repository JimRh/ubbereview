import copy
import datetime
from decimal import Decimal

import pytz
from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.rate_sheets.endpoints.rs_rate_v2 import RateSheetRate
from api.models import SubAccount, CarrierAccount, Carrier, RateSheet, API


class RateSheetTests(TestCase):
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
        "ratesheet",
        "ratesheet_lane",
        "city",
    ]

    def setUp(self):
        self._ubbe_request = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "carrier_id": [1],
            "is_metric": True,
            "packages": [
                {
                    "quantity": 1,
                    "length": Decimal("11"),
                    "width": Decimal("11"),
                    "height": Decimal("11"),
                    "weight": Decimal("20"),
                    "package_type": "BOX",
                    "imperial_length": Decimal("4.33"),
                    "imperial_width": Decimal("4.33"),
                    "imperial_height": Decimal("4.33"),
                    "imperial_weight": Decimal("20"),
                    "description": "Quoting",
                }
            ],
            "is_food": False,
            "origin": {
                "address": "1540 Airport Road",
                "city": "TEST",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "SCA",
            },
            "destination": {
                "address": "140 Thad Johnson Road",
                "city": "TEST",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "K1V0R4",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "total_weight": Decimal("20.00"),
            "total_volume": Decimal("20.00"),
            "total_weight_imperial": Decimal("20.71"),
            "total_volume_imperial": Decimal("0.05"),
            "is_dangerous_good": False,
            "is_international": False,
            "pickup": {
                "date": "2021-08-12",
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": User.objects.first(),
                "carrier_accounts": {
                    1: {
                        "account": CarrierAccount.objects.first(),
                        "carrier": Carrier.objects.first(),
                    }
                },
                "air_list": [],
                "ltl_list": [],
                "ftl_list": [],
                "courier_list": [1],
                "sealift_list": [],
            },
        }

    def test_rs_rate(self):
        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=False)

        ret = api.rate()
        self.assertIsInstance(ret, list)

    def test_rs_rate_ltl(self):
        request = copy.deepcopy(self._ubbe_request)
        request["objects"]["courier_list"] = []
        request["objects"]["ltl_list"] = [1]

        api = RateSheetRate(ubbe_request=request, is_sealift=False)

        ret = api.rate()
        self.assertIsInstance(ret, list)

    def test_rs_rate_ftl(self):
        request = copy.deepcopy(self._ubbe_request)
        request["objects"]["courier_list"] = []
        request["objects"]["ftl_list"] = [1]

        api = RateSheetRate(ubbe_request=request, is_sealift=False)

        ret = api.rate()
        self.assertIsInstance(ret, list)

    def test_rs_get_rate_sheets(self):
        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=False)

        ret = api._get_rate_sheets(carrier_ids=self._ubbe_request["carrier_id"])
        sheet = ret[0]

        self.assertIsInstance(ret, list)
        self.assertIsInstance(sheet, RateSheet)
        self.assertEqual("TEST", sheet.origin_city)
        self.assertEqual("TEST", sheet.destination_city)
        self.assertEqual(1, sheet.transit_days)
        self.assertEqual(Decimal("2.22"), sheet.minimum_charge)
        self.assertEqual("13:30", sheet.cut_off_time)
        self.assertEqual("TEST", sheet.service_code)
        self.assertEqual("TEST", sheet.service_name)

    def test_rs_separate_carriers(self):
        api = RateSheetRate(
            ubbe_request=copy.deepcopy(self._ubbe_request), is_sealift=False
        )

        api._separate_carriers()

        self.assertEqual([1], api._couriers)
        self.assertEqual([], api._ltl)
        self.assertEqual([], api._ftl)

    def test_rs_separate_carriers_ltl(self):
        request = copy.deepcopy(self._ubbe_request)
        request["objects"]["courier_list"] = []
        request["objects"]["ltl_list"] = [1]

        api = RateSheetRate(ubbe_request=request, is_sealift=False)
        api._separate_carriers()

        self.assertEquals([], api._couriers)
        self.assertEquals([1], api._ltl)
        self.assertEquals([], api._ftl)

    def test_rs_separate_carriers_ftl(self):
        request = copy.deepcopy(self._ubbe_request)
        request["objects"]["courier_list"] = []
        request["objects"]["ftl_list"] = [1]

        api = RateSheetRate(ubbe_request=request, is_sealift=False)

        api._separate_carriers()

        self.assertEqual([], api._couriers)
        self.assertEqual([], api._ltl)
        self.assertEqual([1], api._ftl)

    def test_rs_rate_normal(self):
        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=False)
        expected = [
            {
                "carrier_id": 1,
                "carrier_name": "BBE",
                "service_code": "TEST",
                "service_name": "TEST",
                "freight": Decimal("2.22"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.29"),
                "tax_percent": Decimal("13.06"),
                "total": Decimal("2.51"),
                "transit_days": 1,
            }
        ]
        ret = api.rate()

        for r in ret:
            del r["delivery_date"]

        self.assertIsInstance(ret, list)
        self.assertEqual(expected, ret)

    def test_rs_formant(self):
        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=False)
        expected = {
            "carrier_id": 1,
            "carrier_name": "BBE",
            "service_code": "TEST",
            "service_name": "TEST",
            "freight": Decimal("2.22"),
            "surcharge": Decimal("0.00"),
            "tax": Decimal("0.29"),
            "tax_percent": Decimal("13.06"),
            "total": Decimal("2.51"),
            "transit_days": 1,
        }
        ret = api._formant(
            sheet=RateSheet.objects.first(),
            freight=Decimal("2.22"),
            surcharges=Decimal("0.00"),
            tax=Decimal("0.29"),
            total=Decimal("2.51"),
        )
        del ret["delivery_date"]

        self.assertIsInstance(ret, dict)
        self.assertDictEqual(expected, ret)

    def test_rs_formant_two(self):
        request = copy.deepcopy(self._ubbe_request)

        request["pickup"] = {
            "date": "2021-08-09",
            "start_time": "10:00",
            "close_time": "17:00",
        }

        api = RateSheetRate(ubbe_request=request, is_sealift=False)
        expected = {
            "carrier_id": 1,
            "carrier_name": "BBE",
            "service_code": "TEST",
            "service_name": "TEST",
            "freight": Decimal("2.22"),
            "surcharge": Decimal("0.00"),
            "tax": Decimal("0.29"),
            "tax_percent": Decimal("13.06"),
            "total": Decimal("2.51"),
            "transit_days": 1,
        }
        ret = api._formant(
            sheet=RateSheet.objects.first(),
            freight=Decimal("2.22"),
            surcharges=Decimal("0.00"),
            tax=Decimal("0.29"),
            total=Decimal("2.51"),
        )

        del ret["delivery_date"]

        self.assertIsInstance(ret, dict)
        self.assertDictEqual(expected, ret)

    def test_rs_formant_three(self):
        request = copy.deepcopy(self._ubbe_request)
        request["pickup"] = {
            "date": "2021-08-12",
            "start_time": "21:00",
            "close_time": "17:00",
        }

        api = RateSheetRate(ubbe_request=request, is_sealift=False)
        expected = {
            "carrier_id": 1,
            "carrier_name": "BBE",
            "service_code": "TEST",
            "service_name": "TEST",
            "freight": Decimal("2.22"),
            "surcharge": Decimal("0.00"),
            "tax": Decimal("0.29"),
            "tax_percent": Decimal("13.06"),
            "total": Decimal("2.51"),
            "transit_days": 1,
        }
        ret = api._formant(
            sheet=RateSheet.objects.first(),
            freight=Decimal("2.22"),
            surcharges=Decimal("0.00"),
            tax=Decimal("0.29"),
            total=Decimal("2.51"),
        )

        del ret["delivery_date"]

        self.assertIsInstance(ret, dict)
        self.assertDictEqual(expected, ret)

    def test_rs_formant_four(self):
        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=False)
        expected = {
            "carrier_id": 1,
            "carrier_name": "BBE",
            "service_code": "TEST",
            "service_name": "TEST",
            "freight": Decimal("2.22"),
            "surcharge": Decimal("0.00"),
            "tax": Decimal("0.29"),
            "tax_percent": Decimal("13.06"),
            "total": Decimal("2.51"),
            "transit_days": -1,
            "delivery_date": "0001-01-01T00:00:00",
        }

        sheet = RateSheet.objects.first()
        sheet.transit_days = -1
        sheet.save()

        ret = api._formant(
            sheet=RateSheet.objects.first(),
            freight=Decimal("2.22"),
            surcharges=Decimal("0.00"),
            tax=Decimal("0.29"),
            total=Decimal("2.51"),
        )

        self.assertIsInstance(ret, dict)
        self.assertDictEqual(expected, ret)

    def test_rs_get_city_alias(self):
        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=False)
        expected = "Edmonton"
        api._carrier_id = 2
        ret = api._get_city_alias(city="Edmonton", province="AB", country="CA")

        self.assertIsInstance(ret, str)
        self.assertEqual(expected, ret)

    # def test_rs_is_next_day_true(self):
    #     request = copy.deepcopy(self._ubbe_request)
    #     tz = pytz.timezone("America/Edmonton")
    #     current_time = datetime.datetime.now(tz)
    #     request["pickup"] = {
    #         "date": current_time.strftime("Y%-%m-%d"),
    #         "start_time": "10:00",
    #         "close_time": "17:00"
    #     }
    #
    #     api = RateSheetRate(ubbe_request=request, is_sealift=False)
    #
    #     self.assertTrue(api._is_next_day)
    #
    # def test_rs_is_next_day_no_pickup(self):
    #     request = copy.deepcopy(self._ubbe_request)
    #
    #     if 'pickup' in request:
    #         del request["pickup"]
    #
    #     api = RateSheetRate(ubbe_request=request, is_sealift=False)
    #
    #     self.assertFalse(api._is_next_day())
    #
    # def test_rs_is_next_day_not_same_day(self):
    #     request = copy.deepcopy(self._ubbe_request)
    #     tz = pytz.timezone("America/Edmonton")
    #     current_time = datetime.datetime.now(tz) + datetime.timedelta(days=1)
    #     request["pickup"] = {
    #         "date": current_time.strftime("Y%-%m-%d"),
    #         "start_time": "10:00",
    #         "close_time": "17:00"
    #     }
    #
    #     api = RateSheetRate(ubbe_request=request, is_sealift=False)
    #
    #     self.assertFalse(api._is_next_day())

    def test_rs_sealift(self):
        request = copy.deepcopy(self._ubbe_request)
        request["carrier_id"] = [41]
        request["sailings"] = [
            "First Sailing - 2020/05/27:FI",
            "Third Sailing - 2020/11/25:TH",
        ]
        request["packages"] = [
            {
                "quantity": 1,
                "length": Decimal("11"),
                "width": Decimal("11"),
                "height": Decimal("11"),
                "weight": Decimal("1200"),
                "package_type": "BOX",
                "imperial_length": Decimal("4.33"),
                "imperial_width": Decimal("4.33"),
                "imperial_height": Decimal("4.33"),
                "imperial_weight": Decimal("1250"),
                "description": "Quoting",
            }
        ]

        request["mid_o"] = {
            "address": "6565 Hébert Boulevard",
            "city": "Ste Catherine",
            "province": "QC",
            "country": "CA",
            "postal_code": "J5C1B5",
            "port": "Ste Catherine",
            "base": "SCA",
        }

        request["mid_d"] = {
            "address": "140 Thad Johnson Road",
            "city": "Arviat",
            "company_name": "KENNETH CARMICHAEL",
            "country": "CA",
            "postal_code": "X0C0E0",
            "province": "NU",
            "has_shipping_bays": True,
            "base": "BBE",
        }

        expected = [
            {
                "carrier_id": 41,
                "carrier_name": "NSSI",
                "service_code": "FISCA",
                "service_name": "First Sailing - 2020/05/27",
                "freight": Decimal("2.22"),
                "crate_cost": Decimal("0.00"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.29"),
                "tax_percent": Decimal("13.06"),
                "total": Decimal("2.51"),
                "transit_days": 1,
                "mid_o": {
                    "address": "6565 Hébert Boulevard",
                    "city": "Ste Catherine",
                    "province": "QC",
                    "country": "CA",
                    "postal_code": "J5C1B5",
                    "port": "Ste Catherine",
                    "base": "SCA",
                },
                "mid_d": {
                    "address": "140 Thad Johnson Road",
                    "city": "Arviat",
                    "company_name": "KENNETH CARMICHAEL",
                    "country": "CA",
                    "postal_code": "X0C0E0",
                    "province": "NU",
                    "has_shipping_bays": True,
                    "base": "BBE",
                },
            },
            {
                "carrier_id": 41,
                "carrier_name": "NSSI",
                "service_code": "THSCA",
                "service_name": "Third Sailing - 2020/11/25",
                "freight": Decimal("2.22"),
                "crate_cost": Decimal("0.00"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.29"),
                "tax_percent": Decimal("13.06"),
                "total": Decimal("2.51"),
                "transit_days": 1,
                "mid_o": {
                    "address": "6565 Hébert Boulevard",
                    "city": "Ste Catherine",
                    "province": "QC",
                    "country": "CA",
                    "postal_code": "J5C1B5",
                    "port": "Ste Catherine",
                    "base": "SCA",
                },
                "mid_d": {
                    "address": "140 Thad Johnson Road",
                    "city": "Arviat",
                    "company_name": "KENNETH CARMICHAEL",
                    "country": "CA",
                    "postal_code": "X0C0E0",
                    "province": "NU",
                    "has_shipping_bays": True,
                    "base": "BBE",
                },
            },
        ]
        api = RateSheetRate(ubbe_request=request, is_sealift=True)
        ret = api.rate()

        self.assertIsInstance(ret, list)
        self.assertEqual(expected, ret)

    def test_rs_sealift_fail(self):
        request = copy.deepcopy(self._ubbe_request)
        request["carrier_id"] = [41]
        request["sailings"] = [
            "First Sailing - 2020/05/27:FI",
            "Third Sailing - 2020/11/25:TH",
        ]
        request["packages"] = [
            {
                "quantity": 1,
                "length": Decimal("11"),
                "width": Decimal("11"),
                "height": Decimal("11"),
                "weight": Decimal("12"),
                "package_type": "BOX",
                "imperial_length": Decimal("4.33"),
                "imperial_width": Decimal("4.33"),
                "imperial_height": Decimal("4.33"),
                "imperial_weight": Decimal("12"),
                "description": "Quoting",
            }
        ]

        expected = []
        api = RateSheetRate(ubbe_request=request, is_sealift=True)
        ret = api.rate()

        self.assertIsInstance(ret, list)
        self.assertEqual(expected, ret)

    def test_rs_sealift_off(self):
        rs = API.objects.get(name="Sealift")
        rs.active = False
        rs.save()

        api = RateSheetRate(ubbe_request=self._ubbe_request, is_sealift=True)

        ret = api.rate()
        self.assertIsInstance(ret, list)
        self.assertEqual([], ret)
