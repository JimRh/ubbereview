"""
    Title: Celery Business Central
    Description: This file will contain functions for Celery Business Central.
    Created: May 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from time import sleep

from django.core.exceptions import ObjectDoesNotExist

from api.apis.business_central.business_central import BusinessCentral
from api.apis.business_central.jobs.bc_job_task_deliver import BCJobTaskDeliver
from api.exceptions.project import ViewException
from brain.celery import app


class CeleryBusinessCentral:
    """
        Push information into business central behind the scenes.
    """

    @app.task(bind=True)
    def update_created_file(self, data: dict):
        from api.models import Shipment

        sleep(2)

        try:
            shipment = Shipment.objects.get(shipment_id=data["shipment_id"])
        except ObjectDoesNotExist as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 52", message=str(e))
            return None

        try:
            res = BusinessCentral().update_created_file(data=data, shipment=shipment)
        except ViewException as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 65", message=str(e.message))
            return None

    @app.task(bind=True)
    def update_created_account_file(self, data: dict):
        from api.models import Shipment

        sleep(2)

        try:
            shipment = Shipment.objects.get(shipment_id=data["shipment_id"])
        except ObjectDoesNotExist as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 52", message=str(e))
            return None

        try:
            res = BusinessCentral().update_account_file(data=data, shipment=shipment)
        except ViewException as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 65", message=str(e.message))
            return None

    @app.task(bind=True)
    def update_job_file(self, data: dict):

        from api.models import Shipment

        sleep(2)

        try:
            shipment = Shipment.objects.get(shipment_id=data["shipment_id"])
        except ObjectDoesNotExist as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 52", message=str(e))
            return None

        try:
            res = BusinessCentral().update_job_file(data=data, shipment=shipment)
        except ViewException as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 65", message=str(e.message))
            return None

    @app.task(bind=True)
    def update_account_ff_file(self, data: dict):

        from api.models import Shipment

        sleep(4)

        try:
            shipment = Shipment.objects.get(shipment_id=data["shipment_id"])
        except ObjectDoesNotExist as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 52", message=str(e))
            return None

        try:
            res = BusinessCentral().update_existing_job_file(data=data, shipment=shipment)
        except ViewException as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 65", message=str(e.message))
            return None

    @app.task(bind=True)
    def deliver_job_file(self, data: dict):

        sleep(1)

        job_task_deliver = BCJobTaskDeliver(ubbe_data={})
        job_task_deliver.create_bc_connection()

        try:
            response = job_task_deliver.deliver_job_task(data=data)
        except Exception as e:
            # 5 Minute wait time to try again.
            sleep(300)

            try:
                response = job_task_deliver.deliver_job_task(data=data)
            except Exception as e:
                from api.background_tasks.logger import CeleryLogger
                CeleryLogger.l_critical.delay(
                    location="track.py line: 67",
                    message=f"Job Task Deliver unexpected failure: {data['leg_id']} {str(e)}"
                )

    @app.task(bind=True)
    def add_job_note(self, data: dict):
        from api.models import Shipment

        sleep(2)

        try:
            shipment = Shipment.objects.get(shipment_id=data["shipment_id"])
        except ObjectDoesNotExist as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 140", message=str(e))
            return None

        data["bc_job_number"] = shipment.ff_number

        try:
            res = BusinessCentral().create_job_note(data=data, shipment=shipment)
        except ViewException as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 147", message=str(e.message))
            return None

    @app.task(bind=True)
    def add_job_attachment(self, data: dict):
        from api.models import Shipment

        sleep(2)

        try:
            shipment = Shipment.objects.get(shipment_id=data["shipment_id"])
        except ObjectDoesNotExist as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 140", message=str(e))
            return None

        data["bc_job_number"] = shipment.ff_number

        try:
            res = BusinessCentral().add_file_attachment(data=data, shipment=shipment)
        except ViewException as e:
            from api.background_tasks.logger import CeleryLogger
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 147", message=str(e.message))
            return None
