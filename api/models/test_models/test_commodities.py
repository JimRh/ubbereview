from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import Shipment, Commodity


class CommoditiesTests(TestCase):
    fixtures = [
        "user",
        "group",
        "countries",
        "provinces",
        "carriers",
        "contact",
        "addresses",
        'markup',
        'account',
        "subaccount",
        "shipments"
    ]
    shipment = mock.Mock(spec=Shipment)
    shipment._state = Mock()
    commodities_json = {
        "shipment": shipment,
        "description": "TEST",
        "quantity": 7,
        "total_weight": Decimal("10.00"),
        "unit_value": Decimal("10.00"),
        "country_code": "CA",
        "package": 7
    }

    def test_create_empty(self):
        record = Commodity.create()
        self.assertIsInstance(record, Commodity)

    def test_create_full(self):
        record = Commodity.create(self.commodities_json)
        self.assertIsInstance(record, Commodity)

    def test_set_values(self):
        record = Commodity.create()
        record.set_values(self.commodities_json)
        self.assertEqual(record.total_weight, Decimal("10.00"))

    def test_all_fields_verbose(self):
        record = Commodity(**self.commodities_json)
        self.assertEqual(record.description, "TEST")
        self.assertEqual(record.quantity, 7)
        self.assertEqual(record.total_weight, Decimal("10.00"))
        self.assertEqual(record.unit_value, Decimal("10.00"))
        self.assertEqual(record.country_code, "CA")
        self.assertEqual(record.package, 7)
        self.assertIsInstance(record.shipment, Shipment)

    def test_repr(self):
        expected = "< Commodity (TEST: CA, TEST) >"
        record = Commodity.create(self.commodities_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST: CA, TEST"
        record = Commodity.create(self.commodities_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        commodity_json = {
            "shipment": Shipment.objects.get(pk=1),
            "description": "TEST",
            "quantity": 7,
            "total_weight": Decimal("7.7777"),
            "unit_value": Decimal("2.2222"),
            "country_code": "CA"
        }
        record = Commodity(**commodity_json)

        try:
            record.save()
        except ValidationError as e:
            self.fail(e)
        self.assertIsInstance(record.shipment, Shipment)
        self.assertEqual(record.description, "TEST")
        self.assertEqual(record.quantity, 7)
        self.assertEqual(record.total_weight, Decimal("7.78"))
        self.assertEqual(record.unit_value, Decimal("2.22"))
        self.assertEqual(record.country_code, "CA")

    def test_one_step_save(self):
        shipment = Shipment.objects.get(pk=1)
        commodities_json = [
            {
                "shipment": shipment,
                "description": "TEST",
                "quantity": 7,
                "total_weight": Decimal("10.00"),
                "unit_value": Decimal("10.00"),
                "made_in_country_code": "CA"
            },
            {
                "shipment": shipment,
                "description": "TEST",
                "quantity": 7,
                "total_weight": Decimal("10.00"),
                "unit_value": Decimal("10.00"),
                "made_in_country_code": "CA"
            },
            {
                "shipment": shipment,
                "description": "TEST",
                "quantity": 7,
                "total_weight": Decimal("10.00"),
                "unit_value": Decimal("10.00"),
                "made_in_country_code": "CA",
                "package": 7
            }
        ]
        shipment_id = shipment.shipment_id
        Commodity.one_step_save(shipment, commodities_json)
        self.assertTrue(Commodity.objects.filter(shipment__shipment_id=shipment_id, package=1).exists())
        self.assertTrue(Commodity.objects.filter(shipment__shipment_id=shipment_id, package=2).exists())
        self.assertTrue(Commodity.objects.filter(shipment__shipment_id=shipment_id, package=7).exists())

    def test_next_leg_json(self):
        expected = {
            "description": "TEST",
            "made_in_country_code": "CA",
            "package": 7,
            "quantity": 7,
            "quantity_unit_of_measure": "Each",
            "total_weight": Decimal("10.00"),
            "unit_value": Decimal("10.00")
        }
        record = Commodity.create(self.commodities_json)
        self.assertDictEqual(expected, record.next_leg_json())
