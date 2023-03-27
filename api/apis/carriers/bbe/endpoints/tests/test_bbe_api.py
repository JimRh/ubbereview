import copy
from decimal import Decimal

from django.test import TestCase

from api.apis.carriers.bbe.endpoints.bbe_api_v1 import BBEAPI
from api.models import BBELane


class BbeApiTest(TestCase):
    fixtures = [
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
        "fuel_surcharge",
        "bbe_lane",
    ]

    def setUp(self):
        self._gobox_request = {
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "is_metric": False,
            "packages": [
                {
                    "quantity": 1,
                    "description": "TEST",
                    "length": Decimal("73.66"),
                    "width": Decimal("25.40"),
                    "height": Decimal("17.78"),
                    "weight": Decimal("12.70"),
                    "package_type": "BOX",
                    "is_dangerous_good": False,
                    "imperial_length": Decimal("29"),
                    "imperial_width": Decimal("10"),
                    "imperial_height": Decimal("7"),
                    "imperial_weight": Decimal("28"),
                }
            ],
            "is_food": False,
            "is_packing": True,
            "destination": {
                "address": "TEST",
                "city": "TEST",
                "company_name": "TEST",
                "country": "CA",
                "postal_code": "X0E0T0",
                "province": "NT",
                "has_shipping_bays": True,
            },
            "origin": {
                "address": "TEST",
                "city": "TEST",
                "company_name": "TEST",
                "country": "CA",
                "postal_code": "X0E0T0",
                "province": "NT",
                "has_shipping_bays": True,
            },
            "pickup": {
                "start_time": "12:00",
                "date": "2019-05-13",
                "end_time": "14:30",
            },
            "total_weight": Decimal("12.70"),
            "total_volume": Decimal("33265.74"),
            "total_weight_imperial": Decimal("28.00"),
            "total_volume_imperial": Decimal("1.17"),
            "carrier_id": [
                601,
                50,
                1,
                53,
                20,
                127,
                71,
                90,
                7,
                122,
                2,
                95,
                54,
                17,
                650,
                535,
                51,
                502,
                40,
                41,
                670,
                11,
                129,
                52,
                747,
            ],
            "is_dangerous_shipment": False,
        }

    def test_bbe_api_init(self):
        api = BBEAPI(ubbe_request=self._gobox_request)

        self.assertIsInstance(api, BBEAPI)

    def test_get_rate_sheet_rate(self):
        api = BBEAPI(ubbe_request=self._gobox_request)
        sheet = api.get_rate_sheet_rate()

        self.assertIsInstance(sheet, BBELane)

    def test_get_rate_sheet_rate_none(self):
        request = copy.deepcopy(self._gobox_request)
        request["origin"]["postal_code"] = "aSDfgb"
        api = BBEAPI(ubbe_request=request)
        sheet = api.get_rate_sheet_rate()

        self.assertEquals(sheet, None)

    def test_get_rate_sheet_ship(self):
        request = copy.deepcopy(self._gobox_request)
        request["service_code"] = "ST"
        api = BBEAPI(ubbe_request=request)
        sheet = api.get_rate_sheet_ship()

        self.assertIsInstance(sheet, BBELane)

    def test_get_rate_sheet_ship_none(self):
        request = copy.deepcopy(self._gobox_request)
        request["origin"]["postal_code"] = "aSDfgb"
        request["service_code"] = "TEST"
        api = BBEAPI(ubbe_request=request)
        sheet = api.get_rate_sheet_ship()

        self.assertEquals(sheet, None)

    def test_get_freight_cost(self):
        api = BBEAPI(ubbe_request=self._gobox_request)
        sheet = api.get_rate_sheet_rate()

        cost = api._get_freight_cost(sheet=sheet, weight=Decimal("25.00"))

        self.assertEquals(cost, Decimal("25.00"))

    def test_get_freight_cost_flat(self):
        api = BBEAPI(ubbe_request=self._gobox_request)
        sheet = api.get_rate_sheet_rate()
        sheet.is_flat_rate = True
        cost = api._get_freight_cost(sheet=sheet, weight=Decimal("25.00"))

        self.assertEquals(cost, Decimal("25.00"))

    def test_get_fuel_surcharge_cost_dom(self):
        api = BBEAPI(ubbe_request=self._gobox_request)

        cost = api._get_fuel_surcharge_cost(
            freight_cost=Decimal("10.00"), final_weight=Decimal("1.0")
        )

        expected = {
            "carrier_id": 1,
            "cost": Decimal("1.01"),
            "fuel_type": "D",
            "name": "Fuel Surcharge",
            "percentage": Decimal("10.10"),
            "valid_to": "",
            "valid_from": "",
        }

        self.assertEquals(cost, expected)

    def test_get_fuel_surcharge_cost_fail(self):
        request = copy.deepcopy(self._gobox_request)
        request["origin"]["country"] = "Country"

        api = BBEAPI(ubbe_request=request)
        cost = api._get_fuel_surcharge_cost(
            freight_cost=Decimal("10.00"), final_weight=Decimal("1.0")
        )

        expected = {
            "name": "Fuel Surcharge",
            "cost": Decimal("0.00"),
            "percentage": Decimal("0.00"),
        }

        self.assertEquals(cost, expected)
