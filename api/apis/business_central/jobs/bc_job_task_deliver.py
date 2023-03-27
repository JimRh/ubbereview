"""
    Title: Business Central Jobs Task Deliver
    Description: This file will contain all functions to create a Business Central Job Task Deliver.
    Created: May 4, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.db import connection

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase
from api.background_tasks.logger import CeleryLogger


class BCJobTaskDeliver(BCJobBase):
    """
        Deliver Job Task.
    """

    def __init__(self, ubbe_data=dict, shipment=None):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)

    @staticmethod
    def _build_deliver_request(data: dict) -> dict:
        """
            Build Business Central Deliver Request.
            :return:
        """

        ret = {
            "FunctionName": "DeliverJobTask",
            "JobNo": data["job_number"],
            "LegID": data["leg_id"],
            # "WayBillNo": self._ubbe_data["tracking"],
            # "InternalComment": data["detail"]
        }

        if 'delivered_datetime' in data:

            if type(data["delivered_datetime"]) == datetime.datetime:
                date = data["delivered_datetime"].isoformat()
            else:
                date = data["delivered_datetime"]

            ret["ActualArrivalDate"] = date

        return ret

    def deliver_job_task(self, data: dict) -> list:
        """
            Update Business Central Job with delivered status.
            :return:
        """

        if not data.get("job_number"):
            raise BusinessCentralError(message="Job Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            request = self._build_deliver_request(data=data)
        except BusinessCentralError as e:
            connection.close()

            CeleryLogger().l_critical.delay(location="bc_job_task.py line: 179", message=str(data))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to build deliver request. (LEG)",
                data=str(e.message)
            )

        # Post Data to Business Central
        try:
            response = self._post(request=request)
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_task.py line: 191", message=str(data))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to send deliver request.(SEND)", data=str(e.message)
            )

        return response
