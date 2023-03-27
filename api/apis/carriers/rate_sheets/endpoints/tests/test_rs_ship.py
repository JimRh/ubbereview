import copy
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.rate_sheets.endpoints.rs_ship_v2 import RateSheetShip
from api.models import (
    SubAccount,
    CarrierAccount,
    Carrier,
    Dispatch,
    SealiftSailingDates,
)


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
        "test_dispatch",
        "test_bol",
        "ports",
        "sailing_dates",
    ]

    def setUp(self):
        self._ubbe_request = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "pickup": {
                "start_time": "08:00",
                "date": "2021-08-09",
                "end_time": "16:30",
            },
            "origin": {
                "company_name": "TESTING INC",
                "name": "TESTING INC TWO",
                "email": "developer@bbex.com",
                "phone": "7809326245",
                "address": "140 Thad Johnson Private 7",
                "city": "TEST",
                "country": "CA",
                "province": "AB",
                "postal_code": "T9E0V6",
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
            "is_food": False,
            "is_metric": True,
            "bc_fields": {"bc_job_number": "J00034", "bc_username": "SKIP"},
            "total_pieces": Decimal("1"),
            "total_weight": Decimal("10.60"),
            "total_volume": Decimal("1191.02"),
            "total_weight_imperial": Decimal("23.37"),
            "total_volume_imperial": Decimal("0.04"),
            "is_international": False,
            "is_dangerous_goods": False,
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": User.objects.first(),
                "carrier_accounts": {
                    1: {
                        "account": CarrierAccount.objects.first(),
                        "carrier": Carrier.objects.get(code=601),
                    },
                    41: {
                        "account": CarrierAccount.objects.first(),
                        "carrier": Carrier.objects.get(code=601),
                    },
                },
                "sailing": SealiftSailingDates.objects.first(),
            },
            "is_bbe": False,
            "api_client_email": "developer@bbex.com",
            "carrier_id": 1,
            "carrier_name": "BBE",
            "carrier_email": "developer@bbex.com",
            "service_code": "TEST",
            "dg_service": None,
            "order_number": "ub0334041338M",
            "is_pickup": True
        }

    def mocked_rate_sheet_email(*args, **kwargs):
        return None

    @mock.patch(
        "api.apis.carriers.rate_sheets.endpoints.rs_email_v2.RateSheetEmail.manual_email",
        new=mocked_rate_sheet_email,
    )
    def test_rs_ship(self):
        api = RateSheetShip(ubbe_request=self._ubbe_request)

        ret = api.ship()
        self.assertIsInstance(ret, dict)

    def test_rs_get_dispatch_default(self):
        request = copy.deepcopy(self._ubbe_request)

        request["origin"]["city"] = "TEST TEST"

        api = RateSheetShip(ubbe_request=request)

        ret = api._get_dispatch()
        self.assertIsInstance(ret, Dispatch)
        self.assertEqual("Edmonton", ret.location)
        self.assertTrue(ret.is_default)

    def test_rs_get_dispatch_not_default(self):
        request = copy.deepcopy(self._ubbe_request)

        request["origin"]["city"] = "Edmonton"

        api = RateSheetShip(ubbe_request=request)

        ret = api._get_dispatch()
        self.assertIsInstance(ret, Dispatch)
        self.assertEqual("Edmonton", ret.location)
        self.assertTrue(ret.is_default)

    def test_rs_get_bol_number(self):
        api = RateSheetShip(ubbe_request=self._ubbe_request)

        dispatch = Dispatch.objects.first()

        ret = api._get_bol_number(dispatch=dispatch)
        self.assertIsInstance(ret, str)
        self.assertEqual("SAS6033593", ret)

    def test_rs_get_bol_number_none(self):
        api = RateSheetShip(ubbe_request=self._ubbe_request)

        dispatch = Dispatch.objects.last()

        ret = api._get_bol_number(dispatch=dispatch)
        self.assertIsInstance(ret, str)
        self.assertEqual("", ret)

    @mock.patch(
        "api.apis.carriers.rate_sheets.endpoints.rs_email_v2.RateSheetEmail.manual_email",
        new=mocked_rate_sheet_email,
    )
    def test_ts_sealift_ship(self):
        request = copy.deepcopy(self._ubbe_request)

        request["ultimate_origin"] = {
            "company_name": "TESTING INC",
            "name": "TESTING INC TWO",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "address": "140 Thad Johnson Private 7",
            "city": "Edmonton International Airport",
            "country": "CA",
            "province": "AB",
            "postal_code": "T9E0V6",
        }

        request["packages"] = [
            {
                "width": Decimal("10.6"),
                "package_type": "BOX",
                "quantity": 1,
                "length": Decimal("10.6"),
                "package": 1,
                "description": "TEST",
                "height": Decimal("10.6"),
                "weight": Decimal("1250.6"),
                "imperial_length": Decimal("4.17"),
                "imperial_width": Decimal("4.17"),
                "imperial_height": Decimal("4.17"),
                "imperial_weight": Decimal("1200.37"),
                "is_dangerous_good": False,
                "volume": Decimal("0.00119102"),
                "is_last": True,
            }
        ]

        request["ultimate_destination"] = {
            "address": "140 Thad Johnson Road",
            "city": "Arviat",
            "company_name": "KENNETH CARMICHAEL",
            "country": "CA",
            "postal_code": "X0C0E0",
            "province": "NU",
            "name": "TESTING INC TWO",
            "email": "developer@bbex.com",
            "phone": "7809326245",
        }

        request.update(
            {
                "carrier_id": 41,
                "carrier_email": "developer@bbex.com",
                "carrier_name": "NSSI",
                "service_code": "FISCA",
                "service_name": "First Sailing",
            }
        )

        api = RateSheetShip(ubbe_request=request)

        ret = api.ship()
        self.assertIsInstance(ret, dict)
