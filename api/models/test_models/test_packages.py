from decimal import Decimal
from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Shipment, Package


class PackageTests(TestCase):
    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "user",
        "group",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount",
        "shipments"
    ]
    shipment = mock.Mock(spec=Shipment)
    shipment._state = Mock()
    shipment._state.db = None
    package_json = {
        "package_id": "GO1234567890",
        "shipment": shipment,
        "width": Decimal("10.00"),
        "length": Decimal("10.00"),
        "height": Decimal("10.00"),
        "weight": Decimal("10.00"),
        "quantity": 7,
        "freight_class_id": Decimal("10.00"),
        "is_cooler": True,
        "is_frozen": True,
        "description": "TEST",
        "package_type": "BOX"
    }

    def test_create_empty(self):
        record = Package.create()
        self.assertIsInstance(record, Package)

    def test_create_full(self):
        record = Package.create(self.package_json)
        self.assertIsInstance(record, Package)

    def test_set_values(self):
        record = Package.create()
        record.set_values(self.package_json)
        self.assertEqual(record.length, Decimal("10.00"))

    def test_all_fields_verbose(self):
        record = Package(**self.package_json)
        self.assertTrue(record.is_cooler)
        self.assertTrue(record.is_frozen)
        self.assertEqual(record.package_id, "GO1234567890")
        self.assertEqual(record.width, Decimal("10.00"))
        self.assertEqual(record.length, Decimal("10.00"))
        self.assertEqual(record.height, Decimal("10.00"))
        self.assertEqual(record.weight, Decimal("10.00"))
        self.assertEqual(record.quantity, 7)
        self.assertEqual(record.freight_class_id, Decimal("10.00"))
        self.assertEqual(record.description, "TEST")
        self.assertEqual(record.package_type, "BOX")
        self.assertIsInstance(record.shipment, Shipment)

    def test_repr(self):
        expected = "< Package (GO1234567890: 10.00x10.00x10.00, 10.00, BOX) >"
        record = Package.create(self.package_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "GO1234567890: 10.00x10.00x10.00, 10.00, BOX"
        record = Package.create(self.package_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        package_json = {
            "package_id": "GO1234567890",
            "shipment": Shipment.objects.get(pk=1),
            "width": Decimal("10.00"),
            "length": Decimal("10.00"),
            "height": Decimal("10.00"),
            "weight": Decimal("10.00"),
            "quantity": 7,
            "freight_class_id": Decimal("10.00"),
            "is_cooler": True,
            "is_frozen": True,
            "description": "TEST",
            "package_type": "BOX"
        }
        record = Package(**package_json)
        record.save()

        self.assertIsInstance(record.shipment, Shipment)

    def test_one_step_save(self):
        packages_json = [
            {
                "width": Decimal("10.00"),
                "length": Decimal("10.00"),
                "height": Decimal("10.00"),
                "weight": Decimal("10.00"),
                "quantity": 2,
                "description": "TEST"
            },
            {
                "width": Decimal("10.00"),
                "length": Decimal("10.00"),
                "height": Decimal("10.00"),
                "weight": Decimal("10.00"),
                "quantity": 2,
                "description": "TEST"
            }
        ]
        shipment = Shipment.objects.get(pk=1)
        shipment_id = shipment.shipment_id
        Package.one_step_save(packages_json, shipment)
        self.assertTrue(Package.objects.filter(package_id=shipment_id + "-1").exists())
        self.assertTrue(Package.objects.filter(package_id=shipment_id + "-2").exists())

    def test_next_leg_json(self):
        expected = {
            "width": Decimal("10.00"),
            "length": Decimal("10.00"),
            "height": Decimal("10.00"),
            "weight": Decimal("10.00"),
            'imperial_height': Decimal('3.94'),
            'imperial_length': Decimal('3.94'),
            'imperial_weight': Decimal('22.05'),
            'imperial_width': Decimal('3.94'),
            "quantity": 7,
            "description": "TEST",
            "is_cooler": True,
            'is_dangerous_good': False,
            "is_frozen": True,
            "package_type": "BOX"
        }
        record = Package(**self.package_json)

        self.assertDictEqual(expected, record.next_leg_json())
