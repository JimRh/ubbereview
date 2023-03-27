import copy
from decimal import Decimal

import gevent

from django.db import connection
from gevent import Greenlet

from api.apis.multi_modal.ship.ship_common import ShipCommon

from api.apis.services.dangerous_goods.dangerous_goods_ground import DangerousGoodsGround
from api.apis.services.middle_location.middle_location import FindMiddleLocation
from api.background_tasks.emails import CeleryEmail
from api.exceptions.project import ViewException, ShipException, DangerousGoodsException

from api.models import Shipment
from api.utilities.carriers import CarrierUtility


class MultiCarrierGroundShip(ShipCommon):
    """
        ubbe Multi Model Shipping - Determines what mode to ship. IE: Ground, Air, or Sealift
    """

    def __init__(self, gobox_request: dict) -> None:
        super(MultiCarrierGroundShip, self).__init__(gobox_request=gobox_request)
        self.interline_email = ""

    @staticmethod
    def _apply_cross_dock(rate_data: dict):
        """

            :param rate_data:
            :return:
        """
        cost_dock = Decimal("100.0")

        rate_data["surcharges"].append({
            "name": "Cross Dock Fee",
            "cost": cost_dock,
            "percentage": Decimal("0.0")
        })

        rate_data["surcharges_cost"] += cost_dock
        sub_total = rate_data["surcharges_cost"] + rate_data["freight"]
        rate_data["tax"] = sub_total * (rate_data["tax_percent"] / 100)
        rate_data["total"] += sub_total + rate_data["tax"]

    def _get_middle_location(self):
        middle_location = FindMiddleLocation.get_middle_location_by_code(code=self._service["middle_base"])

        if not middle_location:
            connection.close()
            raise ViewException({
                "api.ship.interline.error": f'{self._service["middle_base"]} middle location not found.'
            })

        self.interline_email = copy.deepcopy(middle_location["email"])
        self._middle_location = middle_location

    def _setup(self):
        """
            Setup shipping request for air shipments.
        """
        self._main_carrier = self._gobox_request["objects"]["m_carrier"]
        self._pickup_carrier = self._gobox_request["objects"]["p_carrier"]
        self._delivery_carrier = self._gobox_request["objects"]["d_carrier"]

        # Attempt to get Airbases
        self._get_middle_location()

        self._main_request = copy.deepcopy(self._base)
        self._delivery_request = copy.deepcopy(self._base)

        # Update origin and destination
        self._setup_address(address=self._middle_location, key="destination")

        # First Leg
        self._main_request["carrier_id"] = self._pickup_carrier.code
        self._main_request["carrier_email"] = self._pickup_carrier.email  # TODO - DO I NEED THIS? Dispatch System
        self._main_request["service_code"] = self._service["pickup"]["service_code"]
        self._main_request["destination"] = self._middle_location
        self._main_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
        self._main_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])

        # Second Leg
        self._delivery_request["carrier_id"] = self._delivery_carrier.code
        self._delivery_request["carrier_email"] = self._delivery_carrier.email  # TODO - DO I NEED THIS? Dispatch System
        self._delivery_request["service_code"] = self._service["delivery"]["service_code"]
        self._delivery_request["origin"] = self._middle_location
        self._delivery_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
        self._delivery_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])
        self._delivery_request["is_pickup"] = False

    def _send_requests(self):
        """

            :return:
        """

        shipment = Shipment()
        markup = self._sub_account.markup
        exchange_rate = self._get_exchange_rate()

        pickup_leg, main_leg, delivery_leg = shipment.one_step_save(
            (self._pickup_request, self._main_request, self._delivery_request),
            self._user,
            self._sub_account,
            self._gobox_request["origin"],
            self._gobox_request["destination"]
        )

        if shipment.account_id:
            self.update_packages(shipment=shipment, request_data=self._main_request)
            self.update_packages(shipment=shipment, request_data=self._delivery_request)

        if self._main_request["is_dangerous_goods"]:
            try:
                self._dg_main.clean()

                if self._dg_main.is_shipment_dg:
                    self._dg_main.parse()
            except DangerousGoodsException as e:
                connection.close()
                raise ShipException(e.message)

        # Pickup Leg
        self._main_request["dg_service"] = self._dg_main
        self._main_request['order_number'] = main_leg.leg_id

        pickup_carrier = CarrierUtility().get_ship_api(data=self._main_request)

        # Delivery Leg
        self._delivery_request["dg_service"] = self._dg_main
        self._delivery_request['order_number'] = delivery_leg.leg_id

        delivery_carrier = CarrierUtility().get_ship_api(data=self._delivery_request)

        p_greenlet = Greenlet.spawn(pickup_carrier.ship, order_number=main_leg.leg_id)
        d_greenlet = Greenlet.spawn(delivery_carrier.ship, order_number=delivery_leg.leg_id)

        gevent.joinall([p_greenlet, d_greenlet])

        main_data = self._get_data_from_greenlet(
            leg=main_leg,
            greenlet=p_greenlet,
            markup=markup,
        )

        main_data['pickup_requested'] = self._main_request['is_pickup']
        self._apply_cross_dock(rate_data=main_data)
        main_leg.update_leg(update_params=main_data, exchange_rate=exchange_rate)
        self._response['main_leg'] = main_data

        delivery_data = self._get_data_from_greenlet(
            leg=delivery_leg,
            greenlet=d_greenlet,
            markup=markup,
        )

        delivery_data['pickup_requested'] = self._delivery_request['is_pickup']
        delivery_leg.update_leg(update_params=delivery_data, exchange_rate=exchange_rate, on_hold=True)
        self._response['delivery_leg'] = delivery_data

        self._response['pickup_leg_dropoff_location'] = self._middle_location
        self._response['delivery_leg_pickup_location'] = self._middle_location

        self._response['shipment_id'] = shipment.shipment_id

        if self._user.username == "GoBox":
            self._response['main_leg']["markup"] = main_leg.markup
            self._response['delivery_leg']["markup"] = delivery_leg.markup

        shipment.update()

        return shipment

    def ship(self) -> tuple:
        """

            :return: Shipping Response Dict
        """

        self._setup()

        if self._gobox_request["is_dangerous_goods"]:
            self._dg_main = DangerousGoodsGround(self._main_request)

        shipment = self._send_requests()

        CeleryEmail().interline_email.delay(data=shipment.to_api_json, email=self.interline_email)

        return self._response, shipment
