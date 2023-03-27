from datetime import datetime

import requests
from django import db
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from api.exceptions.project import RequestError, TrackException
from api.globals.carriers import CAN_NORTH
from api.globals.project import SKYLINE_TRACK_URL, DEFAULT_TIMEOUT_SECONDS
from api.models import Leg, CarrierAccount, TrackingStatus


class SkylineTrack:
    @staticmethod
    def post(url: str, data: dict, headers: dict = None):
        try:
            response = requests.post(
                url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS, headers=headers
            )
        except requests.RequestException:
            raise RequestError

        try:
            response.raise_for_status()
            response_data = response.json()
            # If 2Ship ever removes their stack trace, we might still be able to detect the exception message
            if (
                "StackTrace" in response_data
                and response_data["StackTrace"]
                or "ExceptionMessage" in response_data
                and response_data["ExceptionMessage"]
            ):
                raise ValueError()
        except (ValueError, requests.RequestException):
            raise RequestError(response, data)

        return response_data

    @staticmethod
    def _assign_package_data(cn_tracking: dict, items: list, key: str) -> dict:
        """
        Group package data by commodity Id.
        :param cn_tracking: Grouped data
        :param items: Skyline shipmments or containers
        :param key: Key to assign data to.
        :return:
        """

        for item in items:
            if item["CommodityId"] not in cn_tracking:
                cn_tracking[item["CommodityId"]] = {"shipments": [], "containers": []}

            cn_tracking[item["CommodityId"]][key].append(item)

        return cn_tracking

    @staticmethod
    def _get_delivered_date(pickup_date: str) -> datetime:
        """
        Format pickup date from skyline tracking status.
        :return: Datetime
        """
        delivered_datetime = datetime(year=1, month=1, day=1, tzinfo=timezone.utc)

        try:
            delivered_datetime = datetime.strptime(
                pickup_date, "%Y-%m-%dT%H:%M:%S.%f"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                delivered_datetime = datetime.strptime(
                    pickup_date, "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        return delivered_datetime

    def _format_response(self, data: dict) -> list:
        """

        :param data:
        :return:
        """

        delivered_datetime = datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
        tracking = []
        cn_tracking = {}

        shipments = data["data"].get("Shipments")
        containers = data["data"].get("Containers")

        # Get recent flight history
        if shipments:
            cn_tracking = self._assign_package_data(
                cn_tracking=cn_tracking, items=shipments, key="shipments"
            )

        # Get recent locations
        if containers:
            cn_tracking = self._assign_package_data(
                cn_tracking=cn_tracking, items=containers, key="containers"
            )

        for key, value in cn_tracking.items():
            together = f"Package {key} "
            ship_status = ""
            location = ""
            weight = ""
            qty = ""
            status = ""

            # Get latest shipment detail for package
            if value["shipments"]:
                shipment = value["shipments"][-1]

                if shipment["PickedUpBy"]:
                    employee = (
                        shipment["VerifyingEmployeeFirstName"]
                        if shipment["VerifyingEmployeeFirstName"]
                        else ""
                    )
                    ship_status = f'{shipment["PickedUpBy"]}, verified by {employee} on {shipment["PickupDate"]}.'
                    status = "Delivered"
                    delivered_datetime = self._get_delivered_date(
                        pickup_date=shipment["PickupDate"]
                    )
                else:
                    ship_status = f'Flight: {shipment["LegRefNo"]}, Departing {shipment["Departing"]}, {shipment["Origin"]} to {shipment["Destination"]}.'
                    status = "InTransit"

                weight = round(shipment["Kgs"], 2)
                qty = shipment["Pieces"]

            # Get latest container detail for package
            if value["containers"]:
                container = value["containers"][-1]

                if container["WarehouseName"] in ["BBE ESHIP", "Fetchable ESHIP"]:
                    location = f"Awaiting arrival to warehouse."
                    status = "Created"
                else:
                    location = f'Currently in warehouse: {container["WarehouseName"]}.'
                    status = "InTransit"

                weight = round(container["Kgs"], 2)
                qty = container["Pieces"]

            together += f"QTY:{qty} - {weight}kg: "

            if ship_status:
                together += ship_status

            if location:
                if ship_status:
                    together += f"\n{location}"
                else:
                    together += location

            track = {"status": status, "details": together}

            if status == "Delivered":
                track.update(
                    {
                        "delivered_datetime": delivered_datetime,
                        "estimated_delivery_datetime": delivered_datetime,
                    }
                )

            tracking.append(track)

        return tracking

    def track(self, leg: Leg) -> dict:
        tracking_identifier = leg.tracking_identifier
        sub_account = leg.shipment.subaccount

        try:
            account = sub_account.carrieraccount_subaccount.get(carrier__code=CAN_NORTH)
        except ObjectDoesNotExist:
            account = CarrierAccount.objects.get(
                carrier__code=CAN_NORTH, subaccount__is_default=True
            )

        request = {
            "FormNumber": int(tracking_identifier[8:]),
            "API_Key": account.api_key.decrypt(),
        }

        try:
            data = self.post(SKYLINE_TRACK_URL, request)
        except RequestError as e:
            raise TrackException({"skyline.track.error": e})

        if not data:
            raise TrackException(
                {"skyline.track.error": "Tracking was not successful."}
            )

        if not data.get("status") == "ok" or not data.get("data"):
            raise TrackException(
                {"skyline.track.error": "Tracking was not successful."}
            )

        responses = self._format_response(data=data)

        delivered_count = 0
        transit_count = 0
        delivered_datetime = datetime(year=1, month=1, day=1, tzinfo=timezone.utc)

        for status in responses:
            status["leg"] = leg
            try:
                TrackingStatus.create(param_dict=status).save()
            except db.utils.IntegrityError as e:
                # ValidationError occurs if an identical TrackingStatus is already in the database
                if "UNIQUE" in e.args:
                    continue

            if status["status"] == "Delivered":
                delivered_count += 1

                if status["delivered_datetime"] > delivered_datetime:
                    delivered_datetime = status["delivered_datetime"]
            elif status["status"] not in ["Delivered", "Created"]:
                transit_count += 1

        if delivered_count == len(responses):
            leg.delivered_date = delivered_datetime
            leg.is_delivered = True
            leg.is_overdue = False
            leg.is_pickup_overdue = False
            leg.save()

            for pd in Leg.objects.filter(
                shipment=leg.shipment, service_code="PICK_DEL"
            ):
                pd.is_delivered = True
                pd.save()
        elif transit_count == len(responses):
            leg.is_pickup_overdue = False
            leg.save()

        ret = {
            "leg": leg,
            "is_saved": True,
        }

        return ret
