"""
    Title: ubbe Auto Track
    Description: This file will contain functions related to Action Express Api.
    Created: June 8, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist

from api.exceptions.project import ViewException, CancelException
from api.models import Shipment, Leg, CarrierAccount
from api.utilities.carriers import CarrierUtility


class Cancel:
    """
    Cancel Shipment or Leg or Cancel Leg Pickup
    """

    def __init__(self, ubb_request: dict):
        self._ubb_request = ubb_request
        self._sub_account = self._ubb_request["sub_account"]

    @staticmethod
    def _get_carrier_account(sub_account, carrier):
        """
        Get carrier account for sub account and carrier combo and default to
        BBE if none found.
        :param sub_account: Sub Account Object
        :param carrier: Carrier Object
        :return:
        """
        try:
            account = CarrierAccount.objects.get(subaccount=sub_account, carrier=carrier)
        except ObjectDoesNotExist:
            account = CarrierAccount.objects.get(subaccount__is_default=True, carrier=carrier)

        return account

    @staticmethod
    def _get_shipment(**args) -> Shipment:
        """
        Get shipment from args.
        :param args:
        :return:
        """

        try:
            shipment = Shipment.objects.select_related(
                    "subaccount__contact"
                ).prefetch_related(
                    "leg_shipment__carrier"
                ).get(**args)
        except ObjectDoesNotExist:
            raise CancelException(
                code="1005", message="Cancel: Shipment not found.", errors=[{"shipment_id": "Does not exist."}]
            )

        return shipment

    @staticmethod
    def _get_leg(**args) -> Leg:
        """
        Get leg from args.
        :param args:
        :return:
        """

        try:
            leg = Leg.objects.select_related("shipment__subaccount").get(**args)
        except ObjectDoesNotExist:
            raise CancelException(
                code="1005", message="Cancel: Leg not found.", errors=[{"leg_id": "Does not exist."}]
            )

        return leg

    def _cancel_leg(self) -> dict:
        """
        Cancel Leg and pickup if it exists.
        @return:
        """
        ret = {
            "pickup": {}
        }

        if self._sub_account.is_bbe:
            leg = self._get_leg(leg_id=self._ubb_request["leg_id"])
        else:
            leg = self._get_leg(leg_id=self._ubb_request["leg_id"], subaccount=self._sub_account)

        status = leg.tracking_status_leg.last()
        is_moving = False

        if status.status != "Created":
            is_moving = True

        if is_moving:
            raise CancelException(
                code="1005",
                message="Leg is moving",
                errors=[{"shipment_id": "Leg is in progress."}]
            )

        account = self._get_carrier_account(
            sub_account=leg.shipment.subaccount, carrier=leg.carrier
        )

        try:
            api = CarrierUtility.get_ship_api(data={
                "shipment_id": leg.shipment.shipment_id,
                "order_number": leg.shipment.shipment_id,
                "leg": leg,
                "leg_id": leg.leg_id,
                "carrier_id": leg.carrier.code,
                "service_code": leg.service_code,
                "tracking_number": leg.tracking_identifier,
                "pickup_id": leg.carrier_pickup_identifier,
                "objects": {
                    'sub_account': leg.shipment.subaccount,
                    'carrier_accounts': {
                        leg.carrier.code: {
                            'account': account,
                            "carrier": leg.carrier
                        }
                    },
                }
            })
        except ViewException as e:
            raise CancelException(code=e.code, message=e.message, errors=e.errors)

        if leg.carrier_pickup_identifier:
            pickup_ret = api.cancel_pickup()
            ret["pickup"].update(pickup_ret)

        cancel = api.cancel()
        ret.update(cancel)

        leg.is_shipped = False
        leg.on_hold = False
        leg.save()

        return ret

    def _cancel_shipment(self) -> dict:
        """
        Cancel shipment by looping through each leg and cancel them and return all responses.
        @return:
        """
        legs = []

        if self._sub_account.is_bbe:
            shipment = self._get_shipment(shipment_id=self._ubb_request["shipment_id"])
        else:
            shipment = self._get_shipment(shipment_id=self._ubb_request["shipment_id"], subaccount=self._sub_account)

        legs_query = shipment.leg_shipment.all()
        is_moving = False

        for leg in legs_query:
            status = leg.tracking_status_leg.last()

            if status.status != "Created":
                is_moving = True

        if is_moving:
            raise CancelException(
                code="1005",
                message="Shipment is moving",
                errors=[{"shipment_id": "Shipment is in progress."}]
            )

        for leg in legs_query:

            carrier_response = {
                "leg": leg.leg_id,
                "pickup": {},
            }

            account = self._get_carrier_account(
                sub_account=shipment.subaccount, carrier=leg.carrier
            )

            try:
                api = CarrierUtility.get_ship_api(data={
                    "shipment_id": leg.shipment.shipment_id,
                    "leg": leg,
                    "leg_id": leg.leg_id,
                    "carrier_id": leg.carrier.code,
                    "service_code": leg.service_code,
                    "objects": {
                        'sub_account': leg.shipment.subaccount,
                        'carrier_accounts': {
                            leg.carrier.code: {
                                'account': account,
                                "carrier": leg.carrier
                            }
                        },
                    }
                })
            except ViewException as e:
                carrier_response["error"] = e.message
                continue

            try:
                if leg.carrier_pickup_identifier:
                    pickup_ret = api.cancel_pickup()
                    carrier_response["pickup"].update(pickup_ret)

                cancel = api.cancel()
                carrier_response.update(cancel)

                leg.is_shipped = False
                leg.on_hold = False
                leg.save()

            except ViewException as e:
                continue

            legs.append(carrier_response)

        shipment.is_shipped = False
        shipment.is_cancel = True
        shipment.save()

        ret = {
            "shipment_id": shipment.shipment_id,
            "legs": legs,
            "is_canceled": False,
            "message": "Shipment has been canceled"
        }

        return ret

    def cancel(self) -> dict:
        """
        Cancel shipment or leg
        @return:
        """

        if 'leg_id' in self._ubb_request:
            ret = self._cancel_leg()
        else:
            ret = self._cancel_shipment()

        return ret
