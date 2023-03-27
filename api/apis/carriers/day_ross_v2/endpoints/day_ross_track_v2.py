"""
    Title: DayRoss Ship
    Description: This file will contain functions related to Day Ross and Sameday Shipping..
    Created: July 13, 2020
    Author: Carmichael
    Edited By:
    Edited Date:

    Notes:
        - Service Level
            GX is for making a shipment without creating a pickup
            GL is for making a shipment and creating a pickup at the same time

"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from lxml import etree
from zeep import CachingClient, Transport
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import TrackException, NoTrackingStatus
from api.globals.carriers import DAY_N_ROSS, SAMEDAY
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import CarrierAccount, Leg, SubAccount
from brain import settings
from brain.settings import DAYROSS_BASE_URL


class DayRossTrack:
    _dr_history = None
    _dr_client = None
    _dr_ns0 = None
    _url = DAYROSS_BASE_URL
    _division = ""
    _username = ""
    _password = ""

    @property
    def dr_history(self):
        return self._dr_history

    @property
    def dr_client(self):
        return self._dr_client

    @property
    def dr_ns0(self):
        return self._dr_ns0

    def _create_connection(self) -> None:
        """
        Create SOAP request history and client.
        """

        if settings.DEBUG:
            wsdl = "api/apis/carriers/day_ross_v2/wsdl/staging.wsdl"
        else:
            wsdl = "api/apis/carriers/day_ross_v2/wsdl/production.wsdl"

        self._dr_history = HistoryPlugin()
        self._dr_client = CachingClient(
            wsdl,
            transport=Transport(cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS),
            plugins=[self._dr_history],
        )
        self._dr_ns0 = self.dr_client.type_factory("ns0")

    def _get_account(self, carrier_id: int, sub_account: SubAccount) -> None:
        """

        :return:
        """

        if carrier_id == DAY_N_ROSS:
            self._division = "GeneralFreight"

            try:
                account = sub_account.carrieraccount_subaccount.get(
                    carrier__code=DAY_N_ROSS
                )
            except ObjectDoesNotExist:
                account = CarrierAccount.objects.get(
                    carrier__code=DAY_N_ROSS, subaccount__is_default=True
                )

            self._username = account.username.decrypt()
            self._password = account.password.decrypt()
        else:
            self._division = "Sameday"

            try:
                account = sub_account.carrieraccount_subaccount.get(
                    carrier__code=SAMEDAY
                )
            except ObjectDoesNotExist:
                account = CarrierAccount.objects.get(
                    carrier__code=SAMEDAY, subaccount__is_default=True
                )

            self._username = account.username.decrypt()
            self._password = account.password.decrypt()

    def _post(self, tracking_identifier: str):
        """
        Send shipment Request to Day Ross to ship.
        :param request: SOAP shipment request
        :return: response
        """

        try:
            response = self._dr_client.service.GetMovementHistory(
                division=self._division,
                emailAddress=self._username,
                password=self._password,
                shipmentNumber=tracking_identifier,
            )
        except Fault as e:
            connection.close()
            CeleryLogger().l_warning.delay(
                location="day_ross_track.py line: 161",
                message=str(
                    {"api.error.dr.track": "Zeep Failure: {}".format(e.message)}
                ),
            )
            CeleryLogger().l_info.delay(
                location="day_ross_track.py line: 161",
                message="Day and Ross Track request data: {}".format(
                    etree.tounicode(self._dr_history.last_sent["envelope"])
                ),
            )
            CeleryLogger().l_info.delay(
                location="day_ross_track.py line: 161",
                message="Day and Ross Track response data: {}".format(
                    etree.tounicode(self._dr_history.last_received["envelope"])
                ),
            )

            raise TrackException(
                {"api.error.dr.track": "Could not track D&R, request error"}
            )

        return response

    def track(self, leg: Leg):
        """

        :param leg:
        :return:
        """
        tracking_identifier = leg.tracking_identifier

        self._create_connection()
        self._get_account(
            carrier_id=leg.carrier.code, sub_account=leg.shipment.subaccount
        )

        if not tracking_identifier:
            connection.close()
            raise TrackException({"api.error.dr.track": "No tracking number given"})

        try:
            response = self._post(tracking_identifier=tracking_identifier)
        except Exception as e:
            connection.close()
            CeleryLogger().l_warning.delay(
                location="day_ross_track.py line: 161",
                message=str(
                    {"api.error.dr.track": "Track request failed: {}".format(str(e))}
                ),
            )
            raise TrackException(
                {"api.error.dr.track": "Could not track D&R, request error"}
            )

        ret_status = {}
        ret_time = ""
        try:
            for history in response:
                event_time = history["EventTime"]
                event_code = history["EventCode"].strip()
                description = history["Description"]

                if event_code in ["P", "F"]:
                    code = "Delivered"
                elif event_code in ["E"]:
                    code = "OutForDelivery"
                elif event_code in ["A", "W", "T", "ASWEA"]:
                    code = "InTransit"
                elif event_code in ["G"]:
                    code = "Pickup"
                else:
                    code = "Created"

                if not history["CityProv"]:
                    city = ""
                else:
                    city = f', {history["CityProv"]}'

                status = {"leg": leg, "status": code, "details": f"{description}{city}"}

                if code == "Delivered":
                    status["delivered_datetime"] = event_time

                if not ret_status:
                    ret_status = status
                    ret_time = event_time

                if ret_time < event_time:
                    ret_status = status
                    ret_time = event_time
        except Exception as e:
            CeleryLogger().l_critical.delay(
                location="day_ross_track.py line: 195",
                message=str({"api.error.dr.track": "Track format: {}".format(str(e))}),
            )
            raise TrackException(
                {"api.error.dr.track": "Could not track D&R, request error"}
            )

        if not ret_status:
            raise NoTrackingStatus

        return ret_status
