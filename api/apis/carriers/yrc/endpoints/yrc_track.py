"""
    Title: YRC Tracking Api
    Description: This file will contain functions related to YRC Tracking Apis.
    Created: January 20, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from typing import Union

import requests
from django.db import connection
from lxml import etree

from api.apis.carriers.yrc.endpoints.yrc_document import YRCDocument
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, TrackException
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import Leg, ShipDocument


class YRCTrack:
    """
    YRC Track Class
    """

    _url = "http://my.yrc.com/myyrc-api/national/servlet"

    @staticmethod
    def _process_response(response: list) -> dict:
        """
        Process YRC tracking response for the latest status and format into ubbe shipment tracking status.
        :return: dict of latest tracking status
        """

        if len(response) == 0:
            raise TrackException("YRC Track (L34): No Tracking status yet.")

        shipment = response[0]

        if shipment[1].text != "SUCCESS":
            raise TrackException("YRC Track (L34): Not Successful Request.")

        pickup_date = shipment[10].text.lower()
        tendor_code = shipment[13].text
        status_code = shipment[14].text.lower()
        status_message = shipment[16].text
        estimated_delivery_date = shipment[17].text

        if status_code in ["canceled"]:
            code = "Canceled"
        elif status_code in ["delivered"]:
            code = "Delivered"
        elif status_code in ["lld", "ofd"]:
            code = "OutForDelivery"
        elif status_code in [
            "loaded",
            "unloaded",
            "tendered mxex",
            "tendered icmx",
            "ofl",
            "unl",
            "ohd",
            "onh",
            "cls",
            "ldg",
            "enr",
            "spot",
        ]:
            code = "InTransit"
        elif status_code in ["picked up", "fbo"]:
            code = "Pickup"
        else:
            code = "Created"

        if tendor_code:
            details = f"{tendor_code.capitalize()} {status_message}"
        else:
            details = f"{status_message}"

        ret = {
            "status": code,
            "details": details,
            "pickup_date": pickup_date,
        }

        try:
            ret["estimated_delivery_datetime"] = datetime.datetime.strptime(
                estimated_delivery_date, "%m/%d/%Y"
            )
        except Exception:
            pass

        if code == "Delivered":
            delivered_date = f"{shipment[11].text} {shipment[12].text}"
            ret["delivered_datetime"] = datetime.datetime.strptime(
                delivered_date, "%m/%d/%Y %H:%M"
            )

        return ret

    def _get(self, data: dict) -> Union[list, dict]:
        """
        Make YRC tracking call.
        """

        try:
            response = requests.get(
                url=self._url, params=data, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.RequestException as e:
            connection.close()
            raise RequestError(
                None, {"url": self._url, "error": str(e), "data": data}
            ) from e

        if not response.ok:
            connection.close()
            raise RequestError(response, {"url": self._url, "data": data})

        try:
            response = response.text
        except ValueError as e:
            connection.close()
            raise RequestError(
                response, {"url": self._url, "error": str(e), "data": data}
            ) from e

        xml = bytes(bytearray(response, encoding="utf-8"))
        xml = etree.XML(xml)

        connection.close()
        return xml

    def track(self, leg: Leg) -> dict:
        """
        Track YRC shipment.
        :param leg: ubbe leg model.
        :return:
        """

        if not leg.tracking_identifier:
            raise TrackException(f"YRC Track (L113): No Tracking ID,  Data: {str(leg)}")

        params = {
            "CONTROLLER": "com.rdwy.ec.rextracking.http.controller.PublicTrailerHistoryAPIController",
            "PRONumber": leg.tracking_identifier,
            "xml": "Y",
            "version": 1.2,
        }

        try:
            response = self._get(data=params)
        except RequestError as e:
            connection.close()
            raise TrackException(
                f"YRC Track (L125): Track Failure  {str(e)},  Leg: {str(leg)}"
            ) from e

        status = self._process_response(response=response)
        status["leg"] = leg

        if status["status"] == "Delivered":
            try:
                documents = YRCDocument().document(
                    tracking_number=leg.tracking_identifier,
                    pickup_date=status["pickup_date"],
                )

                for document in documents:
                    ShipDocument.add_document(
                        leg=leg,
                        document=document["document"],
                        doc_type=document["type"],
                    )

            except Exception as e:
                CeleryLogger.l_critical(
                    location="yrc_track.py", message=f"YRC Track (L65): {str(e)}"
                )
                return status

        connection.close()
        return status
