"""
    Title: TST CF Express Rate api
    Description: This file will contain functions related to TST CF Express rate Api.
    Created: January 20, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timezone

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from lxml import etree

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_base_v2 import TstCfExpressApi
from api.exceptions.project import RequestError, TrackException
from api.globals.carriers import TST
from api.models import CarrierAccount


class TstCfExpressTrack(TstCfExpressApi):
    """
    TST CF Express Track Class

    Units: Imperial Units are used for this api
    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)

        self._leg = self._ubbe_request["leg"]
        self._tracking_number = self._leg.tracking_identifier

        self._request = {}
        self._response = {}

    def _get_carrier_account(self) -> CarrierAccount:
        """
        Get carrier account for carrier
        :return:
        """
        sub_account = self._leg.shipment.subaccount

        try:
            account = sub_account.carrieraccount_subaccount.get(carrier__code=TST)
        except ObjectDoesNotExist:
            account = CarrierAccount.objects.get(
                carrier__code=TST, subaccount__is_default=True
            )

        return account

    def _build(self) -> None:
        """
        Build Tracking Request for TST-CF endpoint.
        """
        self._request = etree.Element("tracingrequest")

        self._add_auth(request=self._request)

        self._request.append(self._add_child(element="language", value="en"))
        self._request.append(self._add_child(element="tracetype", value="P"))

        item = etree.Element("traceitems")
        item.append(self._add_child(element="item", value=self._tracking_number))
        self._request.append(item)

    def _format_response(self, response: dict) -> None:
        """

        :return:
        """
        trace_item = response["traceitem"]

        is_valid = trace_item.get("valid", "N") == "Y"

        if not is_valid:
            raise TrackException("Not valid tracking number.")

        status = trace_item.get("status", "")

        if "Delivered" in status:
            code = "Delivered"
        elif "Out for delivery" in status:
            code = "OutForDelivery"
        elif (
            "Closed" in status
            or "Loaded" in status
            or "Arrived" in status
            or "Enroute" in status
            or "transit" in status
            or "Currently" in status
        ):
            code = "InTransit"
        elif "Picked" in status or "Pickup" in status:
            code = "Pickup"
        else:
            code = "Created"

        self._response = {"leg": self._leg, "status": code, "details": status}

        if code == "Delivered":
            delivery = trace_item["delivery"]
            status += f', received by {delivery["receivedby"]}'
            delivered = datetime.strptime(
                f'{ delivery["date"]} {delivery["time"]}', "%Y%m%d %I%M"
            ).replace(tzinfo=timezone.utc)

            self._response["details"] = status
            self._response["delivered_datetime"] = delivered.isoformat()

    def track(self) -> dict:
        """

        :return:
        """

        if not self._tracking_number:
            raise TrackException("Tracking Number is 'empty'.")

        self._get_carrier_account()
        self._build()

        try:
            response = self._post(
                url=self._track_url, return_key="traceresults", request=self._request
            )
        except RequestError as e:
            connection.close()
            raise TrackException(
                f"TST-CF Document (L187): Failed Post. {str(e)}"
            ) from e

        try:
            self._format_response(response=response)
        except KeyError as e:
            connection.close()
            raise TrackException(f"2Ship Ship (L367): {str(e)}") from e

        return self._response
