import copy
from decimal import Decimal

from django.test import TestCase

from api.apis.carriers.bbe.endpoints.bbe_rate_v1 import BBERate


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
        "api",
        "ratesheet",
        "ratesheet_lane",
        "fuel_surcharge",
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
                "postal_code": "TEST",
                "province": "AB",
                "has_shipping_bays": True,
            },
            "origin": {
                "address": "TEST",
                "city": "TEST",
                "company_name": "TEST",
                "country": "CA",
                "postal_code": "TEST",
                "province": "AB",
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

    def test_bbe_rate_init(self):
        api = BBERate(ubbe_request=self._gobox_request)

        self.assertIsInstance(api, BBERate)

    # @patch('api.API.Carriers.TwoShip.two_ship_api_v2.TwoShipAPI._two_ship_get_rate', new=mock_test_good)
    def test_bbe_rate_quote(self):
        api = BBERate(ubbe_request=self._gobox_request)
        response = api.rate(is_quote=True)

        expected = [
            {
                "carrier_id": 1,
                "carrier_name": "BBE",
                "service_code": "BBEQUO",
                "service_name": "Quote",
                "freight": Decimal("0.00"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.00"),
                "tax_percent": Decimal("0.00"),
                "total": Decimal("0.00"),
                "transit_days": -1,
            }
        ]

        self.assertListEqual(response, expected)
