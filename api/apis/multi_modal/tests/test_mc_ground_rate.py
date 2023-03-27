import copy

from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.multi_modal.mc_ground_rate import MultiCarrierGroundRate
from api.globals.carriers import UBBE_ML
from api.models import SubAccount
from api.utilities.carriers import CarrierUtility


class MultiCarrierGroundRateTests(TestCase):

    fixtures = [
        'countries',
        'provinces',
        "addresses",
        "contact",
        "user",
        "group",
        "account",
        "carriers",
        "markup",
        "account",
        "subaccount",
    ]

    def setUp(self):

        self.user = User.objects.get(pk=3)
        self.subaccount = SubAccount.objects.first()

        carrier_accounts = CarrierUtility().get_carrier_accounts(
            sub_account=self.subaccount,
            carrier_list=[1, 2]
        )

        self.param = {
            "carrier_id": [1, 2],
            "packages": [
                {
                    "length": Decimal("1.11"),
                    "width": Decimal("1.11"),
                    "height": Decimal("1.11"),
                    "weight": Decimal("1.11"),
                    "quantity": 1
                }
            ],
            "destination": {
                "address": "8812 218 St",
                "city": "Edmonton",
                "company_name": "Personal",
                "country": "CA",
                "postal_code": "T5T4R7",
                "province": "AB"
            },
            "origin": {
                "address": "1759 35 Ave E",
                "city": "Edmonton International Airport",
                "company_name": "BBE",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB"
            },
            "objects": {
                "sub_account": self.subaccount,
                "user": self.user,
                "carrier_accounts": carrier_accounts,
                "air_list": CarrierUtility().get_air(),
                "ltl_list": CarrierUtility().get_ltl(),
                "ftl_list": CarrierUtility().get_ftl(),
                "courier_list": CarrierUtility().get_courier(),
                "sealift_list": CarrierUtility().get_sealift()
            },
            "is_dangerous_goods": False
        }

        self._mcg = MultiCarrierGroundRate(gobox_request=self.param)

    def test_process_carriers(self):
        self._mcg._process_carriers()

        self.assertIsInstance(self._mcg._ground_carriers, list)
        self.assertEqual([1], self._mcg._ground_carriers)

    def test_process_carriers_ubbe_ml(self):
        self._mcg._carrier_id.append(UBBE_ML)
        self._mcg._process_carriers()

        self.assertIsInstance(self._mcg._ground_carriers, list)
        self.assertEqual([1], self._mcg._ground_carriers)

    def test_get_cheapest(self):
        test = [
            {"total": 10},
            {"total": 11},
            {"total": 12},
            {"total": 13},
        ]

        rate = self._mcg._get_cheapest(rate_data=test)

        self.assertIsInstance(rate, dict)
        self.assertEqual({"total": 10}, rate)

    def test_get_cheapest_two(self):
        test = [
            {"total": 10},
            {"total": 11},
            {"total": 12},
            {"total": 3},
        ]

        rate = self._mcg._get_cheapest(rate_data=test)

        self.assertIsInstance(rate, dict)
        self.assertEqual({"total": 3}, rate)

    def test_set_address_origin(self):
        request = copy.deepcopy(self.param)

        self._mcg._middle_location = {
            "address": "E",
            "city": "B",
            "company_name": "B",
            "country": "C",
            "postal_code": "T",
            "province": "A",
            "base": "K"
        }

        expected = {'address': 'E', 'city': 'B', 'company_name': 'GoBox API', 'country': 'C', 'postal_code': 'T', 'province': 'A', 'base': 'K'}

        self._mcg._set_address(request=request, key="origin")
        self.assertEqual(expected, request["origin"])

    def test_set_address_destination(self):
        request = copy.deepcopy(self.param)

        self._mcg._middle_location = {
            "address": "E",
            "city": "B",
            "company_name": "B",
            "country": "C",
            "postal_code": "T",
            "province": "A",
            "base": "K"
        }

        expected = {'address': 'E', 'city': 'B', 'company_name': 'GoBox API', 'country': 'C', 'postal_code': 'T', 'province': 'A', 'base': 'K'}

        self._mcg._set_address(request=request, key="destination")
        self.assertEqual(expected, request["destination"])
