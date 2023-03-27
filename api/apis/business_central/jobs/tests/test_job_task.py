from django.test import TestCase

from api.apis.business_central.jobs.bc_job_task import BCJobTask
from api.models import Shipment


class BCJobTaskTests(TestCase):

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
        "shipments",
        "legs"
    ]

    test_json = {
        "job_number": "J00123",
        "leg_id": "ub123456780M",
        "status": "Delivered",
        "delivered": "2021-07-09",
        "detail": "Something",
    }

    def setUp(self):
        self.job_task = BCJobTask(ubbe_data=self.test_json, shipment=Shipment.objects.last())

    def test_build_request_legs(self):
        self.job_task._build_request_legs()
        self.assertIsInstance(self.job_task._request_list, list)

    def test_get_carrier_mode_air(self):
        mode_type = self.job_task._get_carrier_mode(mode="AI")
        self.assertIsInstance(mode_type, int)
        self.assertEqual(mode_type, 1)

    def test_get_carrier_mode_ground(self):
        mode_type = self.job_task._get_carrier_mode(mode="CO")
        self.assertIsInstance(mode_type, int)
        self.assertEqual(mode_type, 3)

    def test_get_carrier_sea(self):
        mode_type = self.job_task._get_carrier_mode(mode="SE")
        self.assertIsInstance(mode_type, int)
        self.assertEqual(mode_type, 2)

    def test_get_carrier_mode_ltl(self):
        mode_type = self.job_task._get_carrier_mode(mode="LT")
        self.assertIsInstance(mode_type, int)
        self.assertEqual(mode_type, 3)

    def test_get_carrier_mode_ftl(self):
        mode_type = self.job_task._get_carrier_mode(mode="FT")
        self.assertIsInstance(mode_type, int)
        self.assertEqual(mode_type, 3)

    def test_get_carrier_mode_xx(self):
        mode_type = self.job_task._get_carrier_mode(mode="XX")
        self.assertIsInstance(mode_type, int)
        self.assertEqual(mode_type, 3)
