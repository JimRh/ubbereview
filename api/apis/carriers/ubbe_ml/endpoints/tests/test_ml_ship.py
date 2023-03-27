from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_ship import MLCarrierShip
from api.models import SubAccount, CarrierAccount, Carrier, UbbeMlRegressors


class UbbeMlShipTests(TestCase):
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
        "location_distance",
    ]

    def setUp(self):
        self._ubbe_request = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "carrier_id": 904,
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
                "city": "edmonton international airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "SCA",
            },
            "destination": {
                "address": "140 Thad Johnson Road",
                "city": "ottawa",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "K1V0R4",
                "province": "ON",
                "has_shipping_bays": True,
            },
            "total_weight": Decimal("20.00"),
            "total_volume": Decimal("20.00"),
            "total_weight_imperial": Decimal("20.71"),
            "total_volume_imperial": Decimal("0.05"),
            "is_dangerous_goods": False,
            "is_international": False,
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": User.objects.first(),
                "carrier_accounts": {
                    904: {
                        "account": CarrierAccount.objects.first(),
                        "carrier": Carrier.objects.first(),
                    }
                },
                "air_list": [],
                "ltl_list": [904],
                "ftl_list": [],
                "courier_list": [],
                "sealift_list": [],
            },
        }

        self._ubbe_request_weight_break_2 = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "carrier_id": 904,
            "is_metric": True,
            "packages": [
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
                    "imperial_weight": Decimal("2646"),
                    "description": "Quoting",
                }
            ],
            "is_food": False,
            "origin": {
                "address": "1540 Airport Road",
                "city": "edmonton international airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "SCA",
            },
            "destination": {
                "address": "140 Thad Johnson Road",
                "city": "ottawa",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "K1V0R4",
                "province": "ON",
                "has_shipping_bays": True,
            },
            "total_weight": Decimal("1200"),
            "total_volume": Decimal("20.00"),
            "total_weight_imperial": Decimal("2645.54"),
            "total_volume_imperial": Decimal("0.05"),
            "is_dangerous_goods": False,
            "is_international": False,
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": User.objects.first(),
                "carrier_accounts": {
                    904: {
                        "account": CarrierAccount.objects.first(),
                        "carrier": Carrier.objects.first(),
                    }
                },
                "air_list": [],
                "ltl_list": [904],
                "ftl_list": [],
                "courier_list": [],
                "sealift_list": [],
            },
        }
        UbbeMlRegressors.objects.create()

    def test_ship(self):
        ship = MLCarrierShip(ubbe_request=self._ubbe_request).ship("TEST123456")
        ship.pop("documents")
        self.assertEqual(
            ship,
            {
                "carrier_id": 904,
                "carrier_name": "ubbe LTL",
                "freight": Decimal("198.34"),
                "service_code": "LTL",
                "service_name": "ubbe LTL",
                "surcharges": [],
                "surcharges_cost": Decimal("0.00"),
                "taxes": Decimal("25.78"),
                "tax_percent": Decimal("13.00"),
                "sub_total": Decimal("198.34"),
                "total": Decimal("224.12"),
                "tracking_number": "TEST123456",
                "transit_days": -1,
                "delivery_date": "0001-01-01T00:00:00",
            },
        )

    def test_ship_weight_break_2(self):
        ship = MLCarrierShip(ubbe_request=self._ubbe_request_weight_break_2).ship(
            "TEST123456"
        )
        ship.pop("documents")
        self.assertEqual(
            ship,
            {
                "carrier_id": 904,
                "carrier_name": "ubbe LTL",
                "freight": Decimal("1288.20"),
                "service_code": "LTL",
                "service_name": "ubbe LTL",
                "surcharges": [],
                "surcharges_cost": Decimal("0.00"),
                "taxes": Decimal("167.47"),
                "tax_percent": Decimal("13.00"),
                "sub_total": Decimal("1288.20"),
                "total": Decimal("1455.67"),
                "tracking_number": "TEST123456",
                "transit_days": -1,
                "delivery_date": "0001-01-01T00:00:00",
            },
        )
