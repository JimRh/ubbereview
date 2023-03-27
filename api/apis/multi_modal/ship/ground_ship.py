import copy

from api.apis.multi_modal.ship.ship_common import ShipCommon
from api.apis.services.dangerous_goods.dangerous_goods_ground import DangerousGoodsGround
from api.exceptions.project import ShipException
from api.models import Shipment


class GroundShip(ShipCommon):
    """
        ubbe Multi Model Shipping - Determines what mode to ship. IE: Ground, Air, or Sealift
    """

    def __init__(self, gobox_request: dict) -> None:
        super(GroundShip, self).__init__(gobox_request=gobox_request)

    def _setup(self):
        self._main_request = copy.deepcopy(self._base)
        self._main_request["carrier_id"] = self._main_carrier.code
        self._main_request["carrier_name"] = self._main_carrier.name
        self._main_request["carrier_email"] = self._main_carrier.email
        self._main_request["service_code"] = self._service.get("service_code", "")

    def _send_requests(self):
        shipment = Shipment()

        p_leg, main_leg, d_leg = shipment.one_step_save(
            (self._pickup_request, self._main_request, self._delivery_request),
            self._user,
            self._sub_account,
            self._gobox_request["origin"],
            self._gobox_request["destination"]
        )

        if shipment.account_id:
            self.update_packages(shipment=shipment, request_data=self._main_request)

            if self._pickup_request:
                self.update_packages(shipment=shipment, request_data=self._pickup_request)

            if self._delivery_request:
                self.update_packages(shipment=shipment, request_data=self._delivery_request)

        self._response['pickup_leg'] = None
        self._response['pickup_leg_dropoff_location'] = self._main_request["origin"]
        self._response['delivery_leg'] = None
        self._response['delivery_leg_pickup_location'] = self._main_request['destination']
        self._main_request["dg_service"] = self._dg_main
        self._main_request["order_number"] = main_leg.leg_id

        main_greenlet = self._create_greenlets(order_number=main_leg.leg_id, request=self._main_request)
        markup = self._sub_account.markup

        # Main Leg
        try:
            main_data = self._get_data_from_greenlet(
                leg=main_leg,
                greenlet=main_greenlet,
                markup=markup,
            )
        except ShipException:
            shipment.delete()
            raise

        exchange_rate = self._get_exchange_rate()
        main_data['pickup_requested'] = self._main_request["is_pickup"]
        main_leg.update_leg(update_params=main_data, exchange_rate=exchange_rate)

        self._response['main_leg'] = main_data
        self._response['shipment_id'] = shipment.shipment_id

        if self._user.username == "GoBox":
            self._response["markup"] = markup.default_percentage
            self._response['main_leg']["markup"] = main_leg.markup

        shipment.update()

        return shipment

    def ship(self) -> tuple:
        """

            :return: Shipping Response Dict
        """
        self._main_carrier = self._gobox_request["objects"]["m_carrier"]

        self._setup()

        if self._gobox_request["is_dangerous_goods"]:
            self._dg_main = DangerousGoodsGround(self._main_request)

        shipment = self._send_requests()

        return self._response, shipment
