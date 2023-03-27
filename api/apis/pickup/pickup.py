"""
    Title: Pickup
    Description: This file will contain functions related to Pickup .
    Created: February 8, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import PickupException, ViewException
from api.models import Leg, TrackingStatus, CarrierAccount, Package
from api.utilities.carriers import CarrierUtility


class Pickup:
    """
    Pickup Class
    """

    def __init__(self, ubbe_request: dict):
        self._ubbe_request = ubbe_request
        self.leg_id = self._ubbe_request["leg_id"]

    @staticmethod
    def _save_status(leg: Leg, detail: str) -> None:
        """
        Save leg tracking status for cancel or new booking.
        :return:
        """
        try:
            status = TrackingStatus.create(param_dict={
                "leg": leg,
                "status": "Pickup",
                "details": detail
            })
            status.save()
        except IntegrityError as e:
            CeleryLogger().l_critical.delay(
                location="apis/apis/pickup.py line: 40",
                message=f"{e}"
            )
            pass

    @staticmethod
    def _get_carrier_account(subaccount, carrier):

        try:
            account = CarrierAccount.objects.get(subaccount=subaccount, carrier=carrier)
        except Exception:
            account = CarrierAccount.objects.get(subaccount__is_default=True, carrier=carrier)

        return account

    def _get_leg(self) -> Leg:
        """
        Get Leg Object for pickup request.
        :return:
        """
        # TODO - CLEAN THIS UP, CURRENTLY DO NOT LIKE THIS.

        try:
            leg = Leg.objects.select_related(
                "shipment__subaccount",
                "shipment__sender",
                "shipment__receiver",
                "shipment__user",
                "carrier",
                "origin__province__country",
                "destination__province__country"
            ).get(leg_id=self.leg_id)
        except ObjectDoesNotExist:
            raise PickupException(message=f"Pickup: Leg not found for '{self.leg_id}'.")

        account = self._get_carrier_account(subaccount=leg.shipment.subaccount, carrier=leg.carrier)
        packages = Package.objects.filter(shipment=leg.shipment)
        packages = [p.next_leg_json() for p in packages]
        total_imperial_weight = sum(item['imperial_weight'] for item in packages)
        total_metric_weight = sum(item['weight'] for item in packages)

        o_country = leg.origin.province.country.code
        d_country = leg.destination.province.country.code

        self._ubbe_request.update({
            'shipment_id': leg.shipment.shipment_id,
            'order_number': leg.shipment.shipment_id,
            'leg_id': leg.leg_id,
            "leg": leg,
            "request_date": datetime.date.today().strftime("%Y-%m-%d"),
            "carrier_account": account.account_number.decrypt(),
            "request_email,": leg.shipment.email,
            "api_client_email": leg.shipment.user.email,
            "carrier": leg.carrier.name,
            "carrier_name": leg.carrier.name,
            "is_carrier_metric": leg.carrier.is_kilogram,
            "carrier_id": leg.carrier.code,
            "service_code": leg.service_code,
            "service": leg.service_name,
            "service_name": leg.service_name,
            "tracking_number": leg.tracking_identifier,
            "pickup_id": leg.carrier_pickup_identifier,
            "origin": {
                "address": leg.origin.address,
                "city": leg.origin.city,
                "province": leg.origin.province.code,
                "country": leg.origin.province.country.code,
                "postal_code": leg.origin.postal_code,
                "has_shipping_bays": leg.origin.has_shipping_bays,
                "company_name": leg.shipment.sender.company_name,
                "name": leg.shipment.sender.name,
                "phone": leg.shipment.sender.phone,
                "email": leg.shipment.sender.email
            },
            "destination": {
                "address": leg.destination.address,
                "city": leg.destination.city,
                "province": leg.destination.province.code,
                "country": leg.destination.province.country.code,
                "postal_code": leg.destination.postal_code,
                "has_shipping_bays": leg.destination.has_shipping_bays,
                "company_name": leg.shipment.sender.company_name,
                "name": leg.shipment.sender.name,
                "phone": leg.shipment.sender.phone,
                "email": leg.shipment.sender.email
            },
            "pickup": {
                "date": self._ubbe_request.get("date", ""),
                "start_time": self._ubbe_request.get("start_time", ""),
                "end_time": self._ubbe_request.get("end_time", ""),
            },
            "packages": packages,
            "total_weight": total_metric_weight,
            "total_weight_imperial": total_imperial_weight,
            "reference_one": leg.shipment.reference_one,
            "reference_two": leg.shipment.reference_two,
            "is_metric": True,
            "is_dangerous_goods": leg.shipment.is_dangerous_good,
            "is_international": o_country != d_country,
            "objects": {
                'sub_account': leg.shipment.subaccount,
                'carrier_accounts': {
                    leg.carrier.code: {
                        'account': self._get_carrier_account(subaccount=leg.shipment.subaccount, carrier=leg.carrier),
                        "carrier": leg.carrier
                    }
                },
            }
        })

        return leg

    def _get_carrier_api(self) -> tuple:
        """
        Get carrier api for carrier on requested leg.
        :return: tuple of leg and carrier api.
        """

        leg = self._get_leg()

        try:
            carrier_api = CarrierUtility.get_ship_api(data=self._ubbe_request)
        except ViewException as e:
            raise PickupException(message=f"Pickup: Issue getting carrier api.")

        return leg, carrier_api

    def cancel(self) -> dict:
        """
        Cancel pickup for shipment leg.
        :return: Cancel Pickup Detail Dict
        """

        leg, carrier_api = self._get_carrier_api()
        ret = carrier_api.cancel_pickup()

        if ret["is_canceled"]:
            self._save_status(
                leg=leg,
                detail=f"Pickup with number {leg.carrier_pickup_identifier} has been canceled."
            )
            leg.carrier_pickup_identifier = ""
            leg.save()
        elif ret.get("is_canceled_requested", False):
            self._save_status(
                leg=leg,
                detail=ret["message"]
            )

        return ret

    def update(self) -> dict:
        """
        Update pickup for shipment leg.
        :return: Update Pickup Detail Dict
        """
        ret = {}

        leg, carrier_api = self._get_carrier_api()
        cancel = carrier_api.cancel_pickup()
        pickup = carrier_api.pickup()

        if cancel["is_canceled"] and pickup["pickup_id"]:
            self._save_status(
                leg=leg,
                detail=f"Pickup has been Updated from {leg.carrier_pickup_identifier} to {pickup['pickup_id']}."
            )
            leg.carrier_pickup_identifier = pickup['pickup_id']
            leg.save()
        elif cancel.get("is_canceled_requested", False) and pickup["pickup_id"]:
            self._save_status(
                leg=leg,
                detail=f"Pickup cancel has been requested."
            )
            self._save_status(
                leg=leg,
                detail=f"Pickup has been Updated from {leg.carrier_pickup_identifier} to {pickup['pickup_id']}."
            )
            leg.carrier_pickup_identifier = pickup['pickup_id']
            leg.save()

        ret.update(cancel)
        ret.update(pickup)

        return ret

    def pickup(self) -> dict:
        """
        Book new pickup request for shipment leg.
        :return: Pickup Detail Dict
        """

        leg, carrier_api = self._get_carrier_api()
        ret = carrier_api.pickup()

        if ret["pickup_id"]:
            leg.carrier_pickup_identifier = ret["pickup_id"]
            leg.save()

            self._save_status(
                leg=leg,
                detail=f"Pickup has been booked: {leg.carrier_pickup_identifier}"
            )

        return ret
