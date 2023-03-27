"""
    Title: Business Central Jobs Task
    Description:
        - This file will contain all functions to interact with Business Central integrations.

        - Customers
        - Items
        - Vendors
        - Job Files


    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.cache import cache

from api.apis.business_central.customers.bc_customer import BusinessCentralCustomers
from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.items.bc_items import BusinessCentralItems
from api.apis.business_central.job_list.bc_job_list import BusinessCentralJobList
from api.apis.business_central.jobs.bc_job_attachments import BCJobAttachment
from api.apis.business_central.jobs.bc_job_file import BCJobFile
from api.apis.business_central.jobs.bc_job_note import BCJobNote
from api.apis.business_central.jobs.bc_job_planning import BCJobPlanningLines
from api.apis.business_central.jobs.bc_job_shipment_items import BCJobShipmentItems
from api.apis.business_central.jobs.bc_job_task import BCJobTask
from api.apis.business_central.vendors.bc_vendors import BusinessCentralVendors
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from brain.settings import FIVE_HOURS_CACHE_TTL


class BusinessCentral:
    """
            Business Central Utility Class for all functions.
    """
    data = {}

    def __init__(self, data=None):

        if data is None:
            data = {}

        self.data = data

    @staticmethod
    def get_customers() -> list:
        """
            Get customers from business central and cache them for XX amount of hours.
            :return:
        """
        bc_customers = cache.get('bc_customers')

        if not bc_customers:

            try:
                bc_customers = BusinessCentralCustomers().read_multiple()
            except ViewException as e:
                raise ViewException(code=e.code, message=e.message, errors=e.errors)

            cache.set('bc_customers', bc_customers, FIVE_HOURS_CACHE_TTL)

        return bc_customers

    @staticmethod
    def get_items() -> list:
        """
            Get items from business central and cache them for XX amount of hours.
            :return:
        """

        bc_items = cache.get('bc_items')

        if not bc_items:

            try:
                bc_items = BusinessCentralItems().read_multiple()
            except ViewException as e:
                raise ViewException(code=e.code, message=e.message, errors=e.errors)

            cache.set('bc_items', bc_items, FIVE_HOURS_CACHE_TTL)

        return bc_items

    @staticmethod
    def get_vendors() -> list:
        """
            Get vendors from business central and cache them for XX amount of hours.
            :return:
        """
        bc_vendors = cache.get('bc_vendors')

        if not bc_vendors:

            try:
                bc_vendors = BusinessCentralVendors().read_multiple()
            except ViewException as e:
                raise ViewException(code=e.code, message=e.message, errors=e.errors)

            cache.set('bc_vendors', bc_vendors, FIVE_HOURS_CACHE_TTL)

        return bc_vendors

    @staticmethod
    def get_job_list(username: str, is_all: bool) -> list:
        """
            Get vendors from business central and cache them for XX amount of hours.
            :return:
        """

        if is_all:
            look_up = "bc_job_list"
        else:
            look_up = f"bc_job_list_{username[5:]}"

        bc_job_list = cache.get(look_up)

        if not bc_job_list:

            try:
                bc_job_list = BusinessCentralJobList().read_multiple(username=username, is_all=is_all)
            except ViewException as e:
                raise ViewException(code=e.code, message=e.message, errors=e.errors)

            if is_all:
                cache.set(look_up, bc_job_list, FIVE_HOURS_CACHE_TTL)

        return bc_job_list[::-1]

    @staticmethod
    def create_job_file(data: dict, shipment):
        """
            Create Job File and add Leg information, Shipment Items, Planning Lines, and Attachments.
            :return:
        """

        try:
            job_file = BCJobFile(ubbe_data=data, shipment=shipment).create_file()
            shipment.ff_number = job_file
            shipment.save()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="ship_apis.py line: 96", message=str(e.message))
            raise ViewException(message=e.message)

        data["bc_job_number"] = job_file
        from api.background_tasks.business_central import CeleryBusinessCentral
        CeleryBusinessCentral().update_created_file.delay(data=data)

        return job_file

    @staticmethod
    def update_created_file(data: dict, shipment):
        """

            :param data:
            :param shipment:
            :return:
        """
        try:
            # Create Job Tasks
            j_task = BCJobTask(ubbe_data=data, shipment=shipment)
            j_task.create_bc_connection()
            j_task_response = j_task.create_job_task()

            # Create Planning Lines
            bc_items = BCJobShipmentItems(ubbe_data=data, shipment=shipment)
            bc_items.set_bc_connection(connection=j_task)
            bc_items_response = bc_items.create_shipment_items()

            # Create Planning Lines

            bc_planning = BCJobPlanningLines(ubbe_data=data, shipment=shipment)
            bc_planning.set_bc_connection(connection=j_task)
            bc_planning_response = bc_planning.create_planning_lines()

            # Add Attachments
            bc_attachment = BCJobAttachment(ubbe_data=data, shipment=shipment)
            bc_attachment.set_bc_connection(connection=j_task)
            attachment_response = bc_attachment.create_attachment()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 153", message=str(e.message))

    @staticmethod
    def update_job_file(data: dict, shipment):
        """
            Update Job File with Leg information, Shipment Items, Planning Lines, and Attachments.
            :return:
        """

        try:
            # Create Job Tasks
            j_task = BCJobTask(ubbe_data=data, shipment=shipment)
            j_task.create_bc_connection()
            freight_leg_response = j_task.create_job_task()

            # Create Planning Lines
            bc_planning = BCJobPlanningLines(ubbe_data=data, shipment=shipment)
            bc_planning.set_bc_connection(connection=j_task)
            bc_planning_response = bc_planning.create_planning_lines()

            # Add Attachments
            bc_attachment = BCJobAttachment(ubbe_data=data, shipment=shipment)
            bc_attachment.set_bc_connection(connection=j_task)
            attachment_response = bc_attachment.create_attachment()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 179", message=str(e.message))

    @staticmethod
    def update_account_file(data: dict, shipment):
        """
            Update Account Job File with Leg information, Planning Lines, and Attachments.
            :param data:
            :param shipment:
            :return:
        """

        # Create Planning Lines
        try:
            # Create Job Tasks
            j_task = BCJobTask(ubbe_data=data, shipment=shipment)
            j_task.create_bc_connection()
            freight_leg_response = j_task.create_job_task()

            # Create Planning Lines
            bc_items = BCJobShipmentItems(ubbe_data=data, shipment=shipment)
            bc_items.set_bc_connection(connection=j_task)
            bc_items_response = bc_items.create_shipment_items()

            bc_planning = BCJobPlanningLines(ubbe_data=data, shipment=shipment)
            bc_planning.create_bc_connection()
            bc_planning_response = bc_planning.create_account_planning_lines()

            # Add Attachments
            bc_attachment = BCJobAttachment(ubbe_data=data, shipment=shipment)
            bc_attachment.set_bc_connection(connection=bc_planning)
            attachment_response = bc_attachment.create_attachment()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 80", message=str(e.message))

    @staticmethod
    def create_account_file(data: dict, shipment):
        """

            :param data:
            :param shipment:
            :return:
        """

        data.update({
            "bc_customer": shipment.subaccount.bc_customer_code,
            "bc_username": shipment.subaccount.bc_file_owner,
            "bc_location": shipment.subaccount.bc_location_code,
            "bc_job_number": shipment.subaccount.bc_job_number,
            "bc_customer_reference_one": shipment.reference_one,
            "bc_customer_reference_two": shipment.reference_two,
            "bc_customer_reference_three": "Regular",
            "bc_ubbe_username": "",
            "bc_ubbe_email": ""
        })

        try:
            job_file = BCJobFile(ubbe_data=data, shipment=shipment).create_file(is_account=True)
            shipment.ff_number = job_file
            shipment.save()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="ship_apis.py line: 96", message=str(e.message))
            raise ViewException(message=e.message)

        data["bc_job_number"] = job_file
        from api.background_tasks.business_central import CeleryBusinessCentral
        CeleryBusinessCentral().update_created_account_file.delay(data=data)

        return job_file

    @staticmethod
    def update_existing_job_file(data: dict, shipment):
        """
            Update Job File with Leg information, Shipment Items, Planning Lines, and Attachments.
            :return:
        """

        try:
            # Create Job Tasks
            j_task = BCJobTask(ubbe_data=data, shipment=shipment)
            j_task.create_bc_connection()
            freight_leg_response = j_task.create_job_task()

            # Create Planning Lines
            bc_planning = BCJobPlanningLines(ubbe_data=data, shipment=shipment)
            bc_planning.set_bc_connection(connection=j_task)
            bc_planning_response = bc_planning.create_account_planning_lines()

            # Add Attachments
            bc_attachment = BCJobAttachment(ubbe_data=data, shipment=shipment)
            bc_attachment.set_bc_connection(connection=j_task)
            attachment_response = bc_attachment.create_attachment()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="Tasks.py: Line: 179", message=str(e.message))

    @staticmethod
    def create_job_note(data: dict, shipment):
        """
            Create Job File and add Leg information, Shipment Items, Planning Lines, and Attachments.
            :return:
        """

        try:
            # Create Job Tasks
            j_note = BCJobNote(ubbe_data=data, shipment=shipment)
            j_note.create_bc_connection()

            if data.get("is_transaction", False):
                response = j_note.create_job_note_payment()
            else:
                response = j_note.create_job_note()

        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="ship_apis.py line: 96", message=str(e.message))
            raise ViewException(message=e.message)

    @staticmethod
    def add_file_attachment(data: dict, shipment):
        """
            Add single attachment to a job.
            :return:
        """

        try:
            # Create Job Tasks
            j_attachment = BCJobAttachment(ubbe_data=data, shipment=shipment)
            j_attachment.create_bc_connection()
            response = j_attachment.create_attachment_single()
        except BusinessCentralError as e:
            CeleryLogger().l_critical.delay(location="ship_apis.py line: 96", message=str(e.message))
            raise ViewException(message=e.message)
