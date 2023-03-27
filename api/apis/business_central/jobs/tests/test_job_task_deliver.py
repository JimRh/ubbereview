from django.test import TestCase

from api.apis.business_central.jobs.bc_job_task_deliver import BCJobTaskDeliver


class BCJobTaskDeliverTests(TestCase):

    test_json = {
        "job_number": "J00123",
        "leg_id": "ub123456780M",
        "status": "Delivered",
        "delivered": "2021-07-09",
        "detail": "Something",
    }

    def setUp(self):
        self.job_task_deliver = BCJobTaskDeliver(ubbe_data={})

    def test_build_deliver_request(self):

        data = self.job_task_deliver._build_deliver_request(data=self.test_json)

        self.assertIsInstance(data, dict)
        self.assertEqual(data["JobNo"], "J00123")
        self.assertEqual(data["LegID"], "ub123456780M")
        # self.assertEqual(data["ActualArrivalDate"], "2021-07-09")
        # self.assertEqual(data["InternalComment"], "Something")
