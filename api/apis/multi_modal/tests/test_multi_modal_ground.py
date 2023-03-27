from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from api.models import SubAccount
from api.apis.multi_modal.ground_rate import GroundRate
from api.utilities.carriers import CarrierUtility


class GroundTests(TestCase):
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

    @staticmethod
    def mock_rate():
        return [{
            "carrier_id": 1,
            "freight": Decimal("1.1"),
            "surcharge": Decimal("1.1"),
            "tax": Decimal("1.1"),
            "total": Decimal("1.1")
        },
            {
                "carrier_id": 2,
                "freight": Decimal("1.1"),
                "surcharge": Decimal("1.1"),
                "tax": Decimal("1.1"),
                "total": Decimal("1.1")
            }]

    @patch('api.apis.carriers.union.api_union_v2.Union.rate', new=mock_rate)
    def test_ground_get_rates(self):
        expected = [(None, [{'carrier_id': 1, 'freight': Decimal('1.1'), 'surcharge': Decimal('1.1'), 'tax': Decimal('1.1'), 'total': Decimal('1.1')}], None), (None, [{'carrier_id': 2, 'freight': Decimal('1.1'), 'surcharge': Decimal('1.1'), 'tax': Decimal('1.1'), 'total': Decimal('1.1')}], None)]
        ground = GroundRate(self.param)
        ground._make_requests()
        self.assertEqual(expected, ground._responses)
