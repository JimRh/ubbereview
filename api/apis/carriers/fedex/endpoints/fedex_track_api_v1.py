import datetime

from django.core.exceptions import ObjectDoesNotExist
from lxml import etree
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from api.apis.carriers.fedex.globals.services import TRACK_SERVICE, TRACK_HISTORY
from api.apis.carriers.fedex.soap_objects.track.track_request import TrackRequest
from api.apis.carriers.fedex.utility.utility import FedexUtility
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import TrackException
from api.globals.carriers import FEDEX
from api.models import CarrierAccount, Leg


# TODO: Re-implement tracking


class FedExTrack:
    @staticmethod
    def track(leg: Leg) -> dict:
        sub_account = leg.shipment.subaccount
        tracking_identifier = leg.tracking_identifier

        try:
            # Get account for sub account
            carrier_account = sub_account.carrieraccount_subaccount.get(
                carrier__code=FEDEX
            )
        except ObjectDoesNotExist:
            # Get default account
            carrier_account = CarrierAccount.objects.get(
                carrier__code=FEDEX, subaccount__is_default=True
            )

        track_data = TrackRequest(
            tracking_number=tracking_identifier, carrier_account=carrier_account
        ).data

        try:
            track_response = serialize_object(TRACK_SERVICE.track(**track_data))
            successful, _ = FedexUtility.successful_response(track_response)
        except Fault:
            CeleryLogger().l_debug.delay(
                location="fedex_track_api.py line: 41",
                message=etree.tounicode(
                    TRACK_HISTORY.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_debug.delay(
                location="fedex_track_api.py line: 41",
                message=etree.tounicode(
                    TRACK_HISTORY.last_received["envelope"], pretty_print=True
                ),
            )
            raise TrackException({"fedex.track.error": "Unsuccessful track"})

        track_detail = track_response["CompletedTrackDetails"][0]["TrackDetails"][0]

        if not track_detail["StatusDetail"]:
            raise TrackException({"fedex.track.error": f"No Tracking available."})

        if track_detail["Notification"]["Severity"] == "ERROR":
            raise TrackException(
                {
                    "fedex.track.error": f"Unsuccessful track {track_detail['Notification']['Message']}"
                }
            )

        status_detail = track_detail["StatusDetail"]

        if status_detail["Code"] in ["CA"]:
            code = "Canceled"
        elif status_detail["Code"] in ["DE", "SE"]:
            code = "DeliveryException"
        elif status_detail["Code"] in ["DL"]:
            code = "Delivered"
        elif status_detail["Code"] in ["DD", "OD"]:
            code = "OutForDelivery"
        elif status_detail["Code"] in [
            "AA",
            "AC",
            "AD",
            "AF",
            "AR",
            "AX",
            "CH",
            "DP",
            "DR",
            "DY",
            "EA",
            "ED",
            "EO",
            "EP",
            "FD",
            "HL",
            "IT",
            "IX",
            "LO",
            "OF",
            "OX",
            "PF",
            "PL",
            "RR",
            "RM",
            "RC",
            "RS",
            "RP",
            "LP",
            "RG",
            "RD",
            "SF",
            "SP",
            "TR",
            "CC",
            "CD",
            "CP",
            "EA",
            "SP",
            "CU",
            "BR",
            "TP",
            "CA",
        ]:
            code = "InTransit"
        elif status_detail["Code"] in ["PD", "PM", "PU", "PX", "AP", "DS", "DO"]:
            code = "Pickup"
        else:
            code = "Created"

        resp = {"leg": leg, "status": code, "details": status_detail["Description"]}

        for date in track_detail["DatesOrTimes"]:
            if date["Type"] == "ESTIMATED_DELIVERY":
                try:
                    try:
                        est = datetime.datetime.strptime(
                            date["DateOrTimestamp"], "%Y-%m-%dT%H:%M:%S"
                        )
                    except Exception:
                        est = datetime.datetime.strptime(
                            date["DateOrTimestamp"], "%Y-%m-%dT%H:%M:%S%z"
                        )

                    resp["estimated_delivery_datetime"] = est
                except Exception:
                    continue

        if resp["status"] == "DL":
            delivered = datetime.datetime.strptime(
                track_detail["Events"][-1]["Timestamp"], "%Y-%m-%dT%H:%M:%S%z"
            )
            resp["delivered_datetime"] = delivered

        return resp
