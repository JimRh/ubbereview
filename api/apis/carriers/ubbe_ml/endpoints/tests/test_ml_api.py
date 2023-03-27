from decimal import Decimal

from api.apis.carriers.ubbe_ml.endpoints.ubbe_ml_base import MLCarrierBase
from api.globals.carriers import UBBE_ML
from django.contrib.auth.models import User
from django.test import TestCase

from api.models import SubAccount, CarrierAccount, Carrier, UbbeMlRegressors


class UbbeMlRateTests(TestCase):
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
        "fuel_surcharge",
        "option_name",
        "mandatory_option",
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
            "is_dangerous_good": False,
            "is_international": False,
            "objects": {
                "sub_account": SubAccount.objects.first(),
                "user": User.objects.first(),
                "carrier_accounts": {
                    904: {
                        "account": CarrierAccount.objects.first(),
                        "carrier": Carrier.objects.get(code=904),
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

    def test_init(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        self.assertDictEqual(ml_carier._ubbe_request, self._ubbe_request)
        self.assertDictEqual(
            ml_carier._error_world_request,
            {
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
                "is_dangerous_good": False,
                "is_international": False,
            },
        )

    def test_process_ubbe_data(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        self.assertDictEqual(
            ml_carier._origin,
            {
                "address": "1540 Airport Road",
                "city": "edmonton international airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "base": "SCA",
            },
        )
        self.assertDictEqual(
            ml_carier._destination,
            {
                "address": "140 Thad Johnson Road",
                "city": "ottawa",
                "company_name": "KENNETH CARMICHAEL",
                "country": "CA",
                "postal_code": "K1V0R4",
                "province": "ON",
                "has_shipping_bays": True,
            },
        )
        self.assertListEqual(
            ml_carier._packages,
            [
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
        )
        self.assertEqual(ml_carier._total_quantity, 1)
        self.assertEqual(ml_carier._total_mass_metric, 20.00)
        self.assertEqual(ml_carier._total_volume_metric, 20.00)
        self.assertEqual(ml_carier._total_mass_imperial, Decimal("20.71"))
        self.assertEqual(ml_carier._total_volume_metric, 20.00)
        self.assertTrue(ml_carier._is_metric)
        self.assertEqual(ml_carier._carrier.code, 904)

    def test_clean_error_copy(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        self.assertDictEqual(
            ml_carier._error_world_request,
            {
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
                "is_dangerous_good": False,
                "is_international": False,
            },
        )

    def test_get_fuel_surcharge_cost(self):
        fsc = MLCarrierBase(ubbe_request=self._ubbe_request)._get_fuel_surcharge_cost(
            UBBE_ML, Decimal("20.00"), Decimal("50.50")
        )
        self.assertDictEqual(
            fsc,
            {
                "name": "Fuel Surcharge",
                "carrier_id": 904,
                "cost": Decimal("0.00"),
                "percentage": Decimal("0.00"),
            },
        )
        fsc = MLCarrierBase(ubbe_request=self._ubbe_request)._get_fuel_surcharge_cost(
            1338, Decimal("20.00"), Decimal("50.50")
        )
        self.assertEqual(
            fsc,
            {
                "carrier_id": 1338,
                "name": "Fuel Surcharge",
                "cost": Decimal("0.00"),
                "percentage": Decimal("0.00"),
            },
        )

    def test_get_distance(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        dist = MLCarrierBase._get_distance(ml_carier._origin, ml_carier._destination)
        self.assertEqual(
            str(dist), "edmonton international airport, AB, ottawa, ON, 2846.00"
        )

    def test_taxes(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        tax = ml_carier._get_taxes(Decimal("55.51"), Decimal("21.12"))
        self.assertEqual(tax, Decimal("9.96"))

    def test_get_mandatory_options(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        options = ml_carier._get_mandatory_options(ml_carier._carrier, Decimal("21.12"))
        self.assertEqual(options, [])

    def test_get_all_surcharges(self):
        ml_carier = MLCarrierBase(ubbe_request=self._ubbe_request)
        gas = ml_carier._get_all_surcharges(Decimal("12.12"))
        self.assertTupleEqual(gas, (Decimal("13.70"), Decimal("0.00"), Decimal("1.58")))
