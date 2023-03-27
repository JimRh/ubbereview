"""
    Title: Action Express Tracking Api
    Description: This file will contain functions related to Action Express Tracking Apis.
    Created: June 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.carriers.action_express.endpoints.ac_api import ActionExpressApi
from api.apis.carriers.action_express.endpoints.ac_order import ActionExpressOrder
from api.exceptions.project import RequestError, TrackException
from api.globals.carriers import ACTION_EXPRESS
from api.models import Leg, CarrierAccount


class ActionExpressTrack(ActionExpressApi):
    """
    Action Express Track Class
    """

    _entered = 0
    _submitted = 1
    _in_transit = 2
    _completed = 3
    _cancelled = 4
    _cancelled_billable = 5
    _assigned = 6
    _assigned_in_transit = 7
    _unassigned = 8
    _quoted = 9

    _level_map_description = {
        0: "Entered",
        1: "Submitted",
        2: "In Transit",
        3: "Completed",
        4: "Canceled",
        5: "Canceled (Billable)",
        6: "Assigned",
        7: "Assigned (In Transit)",
        8: "Unassigned",
        9: "Quoted",
    }

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request, is_track=True)

    def _process_response(self, response: list) -> dict:
        """
        Process Action Express tracking response for the latest status and format into ubbe shipment tracking
        status.
        :return: dict of latest tracking status
        """

        if len(response) == 0:
            raise TrackException(
                code="27302",
                message="AE Track (L59): No Tracking status yet.",
                errors=[],
            )

        status = response[-1]

        if status["Level"] in [self._cancelled, self._cancelled_billable]:
            code = "Canceled"
        elif status["Level"] in [self._completed]:
            code = "Delivered"
        elif status["Level"] in [
            self._in_transit,
            self._assigned,
            self._assigned_in_transit,
            self._unassigned,
        ]:
            code = "InTransit"
        elif status["Level"] in [self._entered]:
            code = "Pickup"
        else:
            code = "Created"

        ret = {"status": code, "details": self._level_map_description[status["Level"]]}

        if code == "Delivered":
            ret["delivered_datetime"] = (
                datetime.datetime.now().replace(microsecond=0).isoformat()
            )

        return ret

    def _get_carrier_account(self, sub_account) -> None:
        """
        Get carrier account to api key to track shipment with.
        :param sub_account: ubbe sub account
        """

        try:
            # Get account for sub account
            self._carrier_account = CarrierAccount.objects.get(
                subaccount=sub_account, carrier__code=ACTION_EXPRESS
            )
        except ObjectDoesNotExist:
            # Get default account
            self._carrier_account = CarrierAccount.objects.get(
                carrier__code=ACTION_EXPRESS, subaccount__is_default=True
            )

    def track(self, leg: Leg) -> dict:
        """
        Track Action Express shipment.
        :param leg: ubbe leg model.
        :return:
        """

        self._get_carrier_account(sub_account=leg.shipment.subaccount)
        self._auth = {"Authorization": self._carrier_account.api_key.decrypt()}

        if not leg.carrier_api_id:
            raise TrackException(
                code="27300",
                message=f"AE Track (L112): No Tracking ID,  Data: {str(leg)}",
                errors=[],
            )

        try:
            response = self._get(
                url=self._url + f"/orderStatusChanges/{leg.carrier_api_id}"
            )
        except RequestError as e:
            connection.close()
            raise TrackException(
                code="27301",
                message=f"AE Track (L115): Track Failure  {str(e)},  Data: {str(leg)}",
                errors=[],
            ) from e

        status = self._process_response(response=response)
        status["leg"] = leg

        try:
            if status["status"] in ["InTransit", "Delivered"]:
                tz = pytz.timezone("America/Edmonton")
                detail = ""
                track_type = ""
                date = None
                order = ActionExpressOrder(ubbe_request={}).get_order(
                    api_tracking_id=leg.carrier_api_id,
                    carrier_account=self._carrier_account,
                )

                if status["status"] == "InTransit":
                    detail = order["CollectionContactName"]
                    date = datetime.datetime.strptime(
                        order["CollectionArrivalDate"], "%Y-%m-%dT%H:%M:%S"
                    )
                    track_type = "Picked up from "
                elif status["status"] == "Delivered":
                    detail = order["DeliveryContactName"]
                    date = datetime.datetime.strptime(
                        order["DeliveryArrivalDate"], "%Y-%m-%dT%H:%M:%S"
                    )
                    track_type = "Delivered to"

                if not detail:
                    connection.close()
                    return status

                aware = date.astimezone(tz=tz)
                status[
                    "details"
                ] = f'{status["details"]} - {track_type} {detail} @ {aware.strftime("%Y-%m-%d %H:%M")}'

        except TrackException:
            connection.close()
            return status
        except Exception:
            connection.close()
            return status

        connection.close()
        return status
