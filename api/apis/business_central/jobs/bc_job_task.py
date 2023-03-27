"""
    Title: Business Central Jobs Task
    Description: This file will contain all functions to create a Business Central Job Task.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase
from api.background_tasks.logger import CeleryLogger
from api.utilities.date_utility import DateUtility


class BCJobTask(BCJobBase):
    """
            Create or Modify Job Task.
    """

    def __init__(self, ubbe_data: dict, shipment):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)
        self._request_list = []
        self._leg_count = 0

    def _build_request_legs(self):
        """
            Create request per each leg.
            :return:
        """
        previous_leg = None
        legs = self._shipment.leg_shipment.all()
        self._leg_count = len(legs)

        for leg in legs:
            self._request_list.append(self._create_request(leg=leg, previous_leg=previous_leg))
            previous_leg = leg

    def _get_carrier_mode(self, mode: str):
        """
            Determine carrier mode for nav.
            :param mode: str: ubbe database value
            :return: Nav mode id
        """

        if mode == self._air:
            return self._nav_air
        elif mode in [self._courier, self._ltl, self._ftl]:
            return self._nav_ground_truck
        elif mode == self._sealift:
            return self._nav_water

        return self._nav_ground_truck

    def _create_request(self, leg, previous_leg) -> dict:
        """
            Create request to create a new freight leg.
        """
        from api.models import BBECityAlias

        o_province = leg.origin.province
        d_province = leg.destination.province

        origin_city = BBECityAlias.check_alias(
            alias=leg.origin.city, province_code=o_province.code, country_code=o_province.country.code
        )

        destination_city = BBECityAlias.check_alias(
            alias=leg.destination.city, province_code=d_province.code, country_code=d_province.country.code
        )

        origin = "{},{},{}".format(origin_city, o_province.code, o_province.country.code)
        dest = "{},{},{}".format(destination_city, d_province.code, d_province.country.code)

        request = {
            "FunctionName": "CreateJobTask",
            "JobNo": self._job_number,
            "LegID": leg.leg_id,
            "Description": f"Transportation",
            "DepartureLocation": origin,
            "DestinationLocation": dest,
            "WayBillNo": leg.tracking_identifier,
            "ActualDepartureDate": "",
            "EstimatedArrivalDate": leg.estimated_delivery_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "ActualArrivalDate": "",
            "Mode": self._get_carrier_mode(mode=leg.carrier.mode),
            "CarrierName": leg.carrier.name,
            "CurrentStatus": "Created",
            "InternalComment": leg.carrier_pickup_identifier,
            "ConsignedToCompanyName": leg.leg_id,
        }

        if self._shipment.requested_pickup_time.strftime('%Y-%m-%d') in ["0001-01-01", "1-01-01"]:
            pickup_date = self._shipment.creation_date.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            pickup_date = self._shipment.requested_pickup_time.strftime("%Y-%m-%dT%H:%M:%S")

        if self._leg_count > 1:
            if leg.type == "P":
                est_departure = pickup_date
            elif previous_leg is None and leg.type == "M":
                est_departure = pickup_date
            elif previous_leg.estimated_delivery_date.strftime("%Y-%m-%dT%H:%M:%S") == "0001-01-01T00:00:00":
                est_departure = ""
            else:
                est_departure = DateUtility().new_next_business_day(
                    country_code=o_province.country.code,
                    prov_code=o_province.code,
                    in_date=previous_leg.estimated_delivery_date
                ).strftime("%Y-%m-%dT%H:%M:%S")

            request.update({
                "EstimatedDepartureDate": est_departure,
            })
        else:
            if leg.type == "M":
                request.update({
                    "EstimatedDepartureDate": pickup_date,
                })

        return request

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

    def create_job_task(self) -> list:
        """
            Create new job task.
            :return: Dictionary with job number
        """

        if not self._job_number:
            raise BusinessCentralError(message="Job Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            self._build_request_legs()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_task.py line: 100", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to build freight leg request. (LEG)",
                data=str(e.message)
            )

        # Post Data to Business Central
        try:
            response = self._send_create_requests()
        except BusinessCentralError as e:
            connection.close()
            CeleryLogger().l_critical.delay(location="bc_job_task.py line: 111", message=str(self._request_list))
            raise BusinessCentralError(
                message=f"{self._job_number}: Failed to send freight leg request.(SEND)", data=str(e.message)
            )

        return response
