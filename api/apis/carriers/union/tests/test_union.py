from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from api.apis.carriers.union.api_union_v2 import Union
from api.models import SubAccount


class APIUnionTests(TestCase):
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
        self.param = {
            "account_number": "3f440e1d-333d-421e-8d1a-b6474b5ab14a",
            "is_metric": True,
            "packages": [
                {
                    "length": Decimal("1.11"),
                    "width": Decimal("1.11"),
                    "height": Decimal("1.11"),
                    "weight": Decimal("1.11"),
                    "quantity": 1,
                    "freight_class_id": "1.1",
                }
            ],
            "destination": {
                "address": "8812 218 St",
                "city": "Edmonton",
                "company_name": "Personal",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB",
            },
            "origin": {
                "address": "1759 35 Ave E",
                "city": "Edmonton International Airport",
                "company_name": "BBE",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
            },
            "total_weight_imperial": Decimal(12),
            "total_volume_imperial": Decimal(12),
        }

        self._subaccount = SubAccount.objects.get(id=1)

    def test_union_creation(self):
        union = Union({"msg": "test"})
        expected = {"msg": "test"}
        self.assertEqual(union.gobox_request, expected)

    def test_union_split_all_apis(self):
        union = Union(
            {
                "carrier_id": [708, 535, 20, 122, 123, 650, 904],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        # self.assertEqual(two_ship, {"carrier_id": [2], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            skyline,
            {
                "carrier_id": [708],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [650],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [20],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(day_ross, {"carrier_id": [123], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            sameday,
            {
                "carrier_id": [123],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [535], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})
        self.assertEqual(
            ubbeml,
            {
                "carrier_id": [904],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal("12"),
                "total_volume_imperial": Decimal("12"),
            },
        )

    def test_union_split_only_skyline(self):
        union = Union(
            {
                "carrier_id": [708],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        self.assertEqual(
            two_ship,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            skyline,
            {
                "carrier_id": [708],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(day_ross, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            sameday,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})
        self.assertEqual(
            ubbeml,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal("12"),
                "total_volume_imperial": Decimal("12"),
            },
        )

    def test_union_split_only_day_and_ross(self):
        union = Union(
            {
                "carrier_id": [122],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        self.assertEqual(
            two_ship,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            skyline,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            day_ross,
            {
                "carrier_id": [122],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            sameday,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})
        self.assertEqual(
            ubbeml,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal("12"),
                "total_volume_imperial": Decimal("12"),
            },
        )

    def test_union_split_only_canadapost(self):
        union = Union(
            {
                "carrier_id": [20],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        self.assertEqual(
            two_ship,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            skyline,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [20],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(day_ross, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            sameday,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})

    def test_union_split_only_manitoulin(self):
        union = Union(
            {
                "carrier_id": [670],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        self.assertEqual(
            two_ship,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            skyline,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [670],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(day_ross, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            sameday,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [535], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})
        self.assertEqual(
            ubbeml,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal("12"),
                "total_volume_imperial": Decimal("12"),
            },
        )

    def test_union_split_only_2ship(self):
        union = Union(
            {
                "carrier_id": [650, 2],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        # self.assertEqual(two_ship, {"carrier_id": [2], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            skyline,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [650],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(day_ross, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            sameday,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})
        self.assertEqual(
            ubbeml,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal("12"),
                "total_volume_imperial": Decimal("12"),
            },
        )

    def test_union_split_none(self):
        union = Union(
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        (
            two_ship,
            skyline,
            rate_sheet,
            sealift,
            canadapost,
            day_ross,
            sameday,
            bbe,
            tst,
            calm,
            puro,
            fedex,
            ubbeml,
            action,
            cargo,
            yrc,
            abf,
            man,
        ) = union._split()
        self.assertEqual(
            two_ship,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            skyline,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            rate_sheet,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            canadapost,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(day_ross, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount,"total_weight_imperial": Decimal(12), "total_volume_imperial": Decimal(12)})
        self.assertEqual(
            sameday,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        self.assertEqual(
            bbe,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            },
        )
        # self.assertEqual(manitoulin, {"carrier_id": [], "origin": {"country": "CA"}, "destination": {"country": "CA"}, "sub_account": self._subaccount})
        self.assertEqual(
            ubbeml,
            {
                "carrier_id": [],
                "origin": {"country": "CA"},
                "destination": {"country": "CA"},
                "sub_account": self._subaccount,
                "total_weight_imperial": Decimal("12"),
                "total_volume_imperial": Decimal("12"),
            },
        )

    @staticmethod
    def mock_ship_call():
        return [{"test": "test"}]

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate")
    @patch("api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate")
    @patch("api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate")
    def test_union_both_called(self, rate_sheet, ship_skyline, ship_two_ship):
        union = Union(
            {
                "carrier_id": [708, 670],
                "origin": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "destination": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
                "packages": [],
                "total_weight": Decimal(10),
                "total_volume": Decimal(10),
            }
        )
        union._rate_call()
        self.assertEqual(ship_skyline.call_count, 1)
        self.assertEqual(ship_two_ship.call_count, 0)
        self.assertEqual(rate_sheet.call_count, 1)

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate")
    @patch("api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate")
    @patch("api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate")
    def test_union_two_ship_called(self, rate_sheet, ship_skyline, ship_two_ship):
        union = Union(
            {
                "carrier_id": [670],
                "origin": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "destination": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
                "packages": [],
                "total_weight": Decimal(10),
                "total_volume": Decimal(10),
            }
        )
        union._rate_call()
        self.assertEqual(ship_skyline.call_count, 0)
        self.assertEqual(ship_two_ship.call_count, 0)
        self.assertEqual(rate_sheet.call_count, 1)

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate")
    @patch("api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate")
    @patch("api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate")
    def test_union_skyline_called(self, rate_sheet, ship_skyline, ship_two_ship):
        union = Union(
            {
                "carrier_id": [708],
                "packages": "",
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        union._rate_call()
        self.assertEqual(ship_skyline.call_count, 1)
        self.assertEqual(ship_two_ship.call_count, 0)
        self.assertEqual(rate_sheet.call_count, 0)

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate")
    @patch("api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate")
    @patch("api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate")
    def test_union_neither_called(self, rate_sheet, ship_skyline, ship_two_ship):
        union = Union({"carrier_id": [], "sub_account": self._subaccount})
        union._rate_call()
        self.assertEqual(ship_skyline.call_count, 0)
        self.assertEqual(ship_two_ship.call_count, 0)
        self.assertEqual(rate_sheet.call_count, 0)

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate", new=mock_ship_call)
    @patch(
        "api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate", new=mock_ship_call
    )
    @patch(
        "api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate",
        new=mock_ship_call,
    )
    def test_union_rate_both(self):
        union = Union(
            {
                "carrier_id": [708, 670],
                "origin": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "destination": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
                "packages": [],
                "total_weight": Decimal(10),
                "total_volume": Decimal(10),
            }
        )
        rate = union.rate()
        self.assertEqual(rate, [{"test": "test"}, {"test": "test"}])

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate", new=mock_ship_call)
    @patch(
        "api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate", new=mock_ship_call
    )
    @patch(
        "api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate",
        new=mock_ship_call,
    )
    def test_union_rate_two_ship(self):
        union = Union(
            {
                "carrier_id": [670],
                "origin": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "destination": {"country": "CA", "city": "Edmonton", "province": "AB"},
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
                "packages": [],
                "total_weight": Decimal(10),
                "total_volume": Decimal(10),
            }
        )
        rate = union.rate()
        self.assertEqual(rate, [{"test": "test"}])

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate", new=mock_ship_call)
    @patch(
        "api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate", new=mock_ship_call
    )
    @patch(
        "api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate",
        new=mock_ship_call,
    )
    def test_union_skyline_ship(self):
        union = Union(
            {
                "carrier_id": [708],
                "packages": "",
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        rate = union.rate()
        self.assertEqual(rate, [{"test": "test"}])

    @patch("api.apis.carriers.twoship.twoship_api.TwoShipApi.rate", new=mock_ship_call)
    @patch(
        "api.apis.carriers.skyline.skyline_api_v3.SkylineApi.rate", new=mock_ship_call
    )
    @patch(
        "api.apis.carriers.rate_sheets.rate_sheet_api.RateSheetApi.rate",
        new=mock_ship_call,
    )
    def test_union_neither_ship(self):
        union = Union(
            {
                "carrier_id": [],
                "objects": {"sub_account": self._subaccount},
                "total_weight_imperial": Decimal(12),
                "total_volume_imperial": Decimal(12),
            }
        )
        rate = union.rate()
        self.assertEqual(rate, [])
