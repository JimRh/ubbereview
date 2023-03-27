"""
    Title: Business Central Jobs Note
    Description: This file will contain all functions to create a Business Central Job Task.
    Created: June 11, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase
from api.background_tasks.logger import CeleryLogger


class BCJobNote(BCJobBase):
    """
        Create Job Note.
    """

    def __init__(self, ubbe_data: dict, shipment):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)
        self._request_list = []
        self._leg_count = 0

    def _create_request(self, note: str) -> None:
        """
            Create request to create a new note.
        """

        request = {
            "FunctionName": "AddNote",
            "JobNo": self._job_number,
            "Note": note,
        }

        self._request_list.append(request)

    def _send_create_requests(self) -> []:
        """
            Send requests to business central.
            :return:
        """
        response_list = []

        for request in self._request_list:
            response = self._post(request=request)
            response_list.append(response)

        return response_list

    def create_job_note_payment(self) -> list:
        """
            Create new job note.
            :return: Dictionary with job number
        """

        if not self._job_number:
            raise BusinessCentralError(message="Job Number empty", data=self._job_number)

        note = f"Public Payment - ubbe Moneris: " \
            f"Trans Id: {self._ubbe_data['transaction_id']}\n Trans Num: " \
            f"{self._ubbe_data['transaction_number']}\nAmount: {self._ubbe_data['transaction_amount']}\nCard: " \
            f"{self._ubbe_data['card_type']}"

        # Build request data to Business Central
        try:
            self._create_request(note=note)
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_note.py line: 100", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to build note request.",
                data=str(e.message)
            )

        # Post Data to Business Central
        try:
            response = self._send_create_requests()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_note.py line: 111", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to send note request.(SEND)", data=str(e.message)
            )

        return response

    def create_job_note(self) -> list:
        """
            Create new job task.
            :return: Dictionary with job number
        """

        if not self._job_number:
            raise BusinessCentralError(message="Job Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            self._create_request(note=self._ubbe_data["note"])
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_note.py line: 100", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to build note request.",
                data=str(e.message)
            )

        # Post Data to Business Central
        try:
            response = self._send_create_requests()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_note.py line: 111", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to send note request.", data=str(e.message)
            )

        return response
