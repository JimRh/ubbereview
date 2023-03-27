"""
    Title: Calm Air Track Class
    Description: This file will contain functions related to Calm Air Track Apis.
    Created: August 20, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from datetime import datetime

import requests
from django.core.exceptions import ObjectDoesNotExist

from django.db import connection
from django.utils import timezone
from lxml import etree

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, TrackException
from api.globals.carriers import CALM_AIR
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import Leg, CarrierAccount, SubAccount


class CalmAirTrack:
    """
    Class will handle all details about a Calm Air rate request and return appropriate data.


    Units: Metric Units are used for this api
    """

    _track_end = "/public/trackAWB"

    @staticmethod
    def _get_account(sub_account: SubAccount) -> CarrierAccount:
        """
        Get Carrier Account relating to shipment.
        :return:
        """
        try:
            account = sub_account.carrieraccount_subaccount.get(carrier__code=CALM_AIR)
        except ObjectDoesNotExist:
            account = CarrierAccount.objects.get(
                carrier__code=CALM_AIR, subaccount__is_default=True
            )

        return account

    @staticmethod
    def _post(params: dict):
        """
        Make Calm Air Track call
        """
        url = "https://cargo.calmair.com/API_Gateway/public/trackAWB"

        try:
            response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException as e:
            connection.close()
            CeleryLogger().l_info.delay(
                location="calm_air_track.py line: 50",
                message=f"Calm Air Track posting data: {params}",
            )
            raise RequestError(None, params) from e

        if not response.ok:
            connection.close()
            CeleryLogger().l_info.delay(
                location="calm_air_track.py line: 58",
                message=f"Calm Air Track posting data: {params} \nCalm Air return data: {response.text}",
            )
            raise RequestError(response, params)

        return etree.fromstring(response.text)

    def track(self, leg: Leg) -> dict:
        """
        Track calm air shipment.
        :param leg: Leg Object
        :return: Latest tracking status for shipment
        """

        tracking_identifier = leg.tracking_identifier
        account = self._get_account(sub_account=leg.shipment.subaccount)

        if not tracking_identifier:
            connection.close()
            raise TrackException(
                code="29300", message="CalmAir: No tracking number given", errors=[]
            )

        try:
            response = self._post(
                params={
                    "access_key": account.contract_number.decrypt(),
                    "awb_no": tracking_identifier,
                }
            )
        except RequestError as e:
            CeleryLogger().l_critical.delay(
                location="calm_air_track.py line: 92",
                message=f"Calm Air Track:s {str(e)}",
            )
            connection.close()
            raise TrackException(
                code="29301", message=f"CalmAir: Track: {str(e)}", errors=[]
            ) from e

        data = response[-1]
        details = str(data[1].text)
        status = details.lower()

        if "delivered" in status:
            code = "Delivered"
        elif "received for shipping" in status:
            code = "Pickup"
        elif (
            "received" in status
            or "available" in status
            or "pickup" in status
            or "loaded" in status
        ):
            code = "InTransit"
        else:
            code = "Created"

        if code == "Created" and "Tracking Information" in status:
            details = "Awaiting arrival to warehouse."

        ret_status = {
            "leg": leg,
            "status": code,
            "details": details,
        }

        if code == "Delivered":
            date = str(data[2].text)
            split = date.split(" ")
            new_date = f"{split[1]} {split[2]}"
            final_date = datetime.strptime(new_date, "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone.utc
            )
            ret_status.update(
                {
                    "delivered_datetime": final_date,
                    "estimated_delivery_datetime": final_date,
                }
            )

        return ret_status
