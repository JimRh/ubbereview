"""
    Title: ABF Tracking Api
    Description: This file will contain functions related to ABF Tracking Apis.
    Created: June 28, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime
from typing import Union

import requests
import xmltodict
from django import db
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.carriers.abf_freight.endpoints.abf_document import ABFDocument
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, TrackException, ViewException
from api.globals.carriers import ABF_FREIGHT
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import Leg, TrackingStatus, ShipDocument, CarrierAccount


class ABFTrack:
    """
    ABF Track Class
    """

    _url = "https://www.abfs.com/xml/tracexml.asp"

    @staticmethod
    def _process_response(response: dict) -> dict:
        """
        Process YRC tracking response for the latest status and format into ubbe shipment tracking status.
        :return: dict of latest tracking status
        """

        if not response["ABF"]:
            raise TrackException("YRC Track (L34): No Tracking status yet.")

        shipment = response["ABF"][0]

        status_code = shipment["SHORTSTATUS2"]
        status_message = shipment["LONGSTATUS"]
        estimated_delivery_date = shipment["EXPECTEDDELIVERYDATE"]

        if status_code in ["canceled"]:
            code = "Canceled"
        elif status_code in ["DEL"]:
            code = "Delivered"
        elif status_code in ["OFDEL"]:
            code = "OutForDelivery"
        elif status_code in ["UNLD"]:
            code = "InTransit"
        elif status_code in ["picked up", "fbo"]:
            code = "Pickup"
        else:
            code = "Created"

        ret = {
            "status": code,
            "details": f"{status_message}",
        }

        try:
            ret["estimated_delivery_datetime"] = datetime.datetime.strptime(
                estimated_delivery_date, "%m/%d/%Y"
            )
        except Exception:
            pass

        if code == "Delivered":
            ret[
                "details"
            ] += f'Signed by: {shipment["DELIVSIGFIRSTNAME"]} {shipment["DELIVSIGLASTNAME"]}'
            delivered_date = f'{shipment["DELIVERYDATE"]} {shipment["DELIVERYTIME"]}'
            ret["delivered_datetime"] = datetime.datetime.strptime(
                delivered_date, "%m/%d/%Y %H:%M"
            )

        return ret

    def _get(self, data: dict) -> Union[list, dict]:
        """
        Make ABF tracking call.
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
            converted_xml = xmltodict.parse(xml_input=response.content)
        except KeyError as e:
            raise RequestError(response, {"url": self._url, "error": str(e)}) from e

        connection.close()
        return converted_xml

    def _get_carrier_account(self, sub_account) -> None:
        """
        Get carrier account to api key to track shipment with.
        :param sub_account: ubbe sub account
        """

        try:
            # Get account for sub account
            self._carrier_account = CarrierAccount.objects.get(
                subaccount=sub_account, carrier__code=ABF_FREIGHT
            )
        except ObjectDoesNotExist:
            # Get default account
            self._carrier_account = CarrierAccount.objects.get(
                carrier__code=ABF_FREIGHT, subaccount__is_default=True
            )

    def track(self, leg: Leg) -> dict:
        """
        Track YRC shipment.
        :param leg: ubbe leg model.
        :return:
        """

        if not leg.tracking_identifier:
            raise TrackException(f"YRC Track (L113): No Tracking ID,  Data: {str(leg)}")

        self._get_carrier_account(sub_account=leg.shipment.subaccount)

        params = {
            "ID": self._carrier_account.api_key.decrypt(),
            "RefNum": leg.tracking_identifier,
            "RefType": "A",
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

        try:
            TrackingStatus.create(param_dict=status).save()
        except db.utils.IntegrityError as e:
            # ValidationError occurs if an identical TrackingStatus is already in the database
            if "UNIQUE" in e.args:
                raise ViewException("Tracking already saved.") from e

        if status["status"] == "Delivered":
            leg.delivered_date = status["delivered_datetime"]
            leg.is_delivered = True
            leg.is_overdue = False
            leg.is_pickup_overdue = False
            leg.save()
        elif status["status"] not in ["Delivered", "Created"]:
            leg.is_pickup_overdue = False
            leg.save()

        ret = {
            "leg": leg,
            "is_saved": True,
        }

        if status["status"] == "Delivered":
            try:
                documents = ABFDocument().document(
                    tracking_number=leg.tracking_identifier,
                    document_types=["DR", "INV"],
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
                return ret

        connection.close()
        return ret
