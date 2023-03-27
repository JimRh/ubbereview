import copy

from django.core.exceptions import ObjectDoesNotExist

from api.apis.multi_modal.ship.ship_common import ShipCommon
from api.apis.services.dangerous_goods.dangerous_goods_ground import DangerousGoodsGround
from api.exceptions.project import ShipException
from api.globals.carriers import MTS, NSSI, NEAS
from api.globals.project import getkey
from api.models import SealiftSailingDates, Shipment


class SealiftShip(ShipCommon):
    """
        ubbe Multi Model Shipping - Determines what mode to ship. IE: Ground, Air, or Sealift
    """

    def __init__(self, gobox_request: dict) -> None:
        super(SealiftShip, self).__init__(gobox_request=gobox_request)

    @staticmethod
    def _get_cargo_packing_station(carrier_id, port_code: str):

        if carrier_id == NEAS and port_code != "CHU":
            return {
                "company_name": "NEAS Cargo Service Center",
                "address": "950 Boul. Cadieux",
                "city": "Valleyfield",
                "province": "QC",
                "country": "CA",
                "postal_code": "J6T6L4",
                "base": port_code
            }
        elif carrier_id == NSSI:
            return {
                "company_name": "Arctic Consultants",
                "address": "10200 Rue Mirabeau",
                "city": "Montreal",
                "province": "QC",
                "country": "CA",
                "postal_code": "H1J1T6",
                "base": port_code
            }
        elif carrier_id == MTS:
            return {
                "company_name": "BBE Edmonton",
                "address": "1759 35 Ave E",
                "city": "Edmonton International Airport",
                "province": "AB",
                "country": "CA",
                "postal_code": "T9E0V6",
                "base": port_code
            }

        return {}

    def _get_sailing(self, sailing: str, port_code: str) -> SealiftSailingDates:

        try:
            sailing = SealiftSailingDates.objects.select_related(
                "port__address__province__country"
            ).get(
                carrier__code=self._main_carrier.code,
                name=sailing,
                port__code=port_code
            )
        except ObjectDoesNotExist as e:
            raise ShipException({
                "api.ship.port.error": "Incorrect service code for carrier: {}".format(self._main_carrier.code)
            })

        return sailing

    def _setup(self):
        """
            Setup shipping request for sealift shipments.
        """
        self._main_request = copy.deepcopy(self._base)
        self._main_request["other_legs"] = {}
        exchange_rate = self._get_exchange_rate()

        service_code = getkey(self._service, "service_code", '')
        port_code = service_code[2:]

        sailing = self._gobox_request["objects"]["sailing"]

        mid_origin = sailing.port.to_json
        self._update_address(address=mid_origin, info=copy.deepcopy(self._base["origin"]))

        if self._pickup_carrier:
            self._pickup_request = copy.deepcopy(self._base)

            cargo = {}
            if self._gobox_request.get("is_packing", False):
                cargo = self._get_cargo_packing_station(carrier_id=self._main_carrier.code, port_code=port_code)

            if cargo:
                self._update_address(address=cargo, info=copy.deepcopy(self._base["origin"]))
                self._pickup_request["destination"] = cargo
            else:
                self._pickup_request["destination"] = mid_origin

            self._main_request["other_legs"]["pickup_carrier"] = self._pickup_carrier.name
            self._main_request["other_legs"]["pickup_carrier_ID"] = self._pickup_carrier.code
            self._pickup_request["carrier_id"] = self._pickup_carrier.code
            self._pickup_request["carrier_email"] = self._pickup_carrier.email
            self._pickup_request["is_pickup"] = False
            self._pickup_request["service_code"] = getkey(self._service, "pickup.service_code", '')
            self._pickup_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
            self._pickup_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])

            if self._appointment_delivery not in self._pickup_request["carrier_options"]:
                self._pickup_request["carrier_options"].append(self._appointment_delivery)

        if self._delivery_carrier:
            self._main_request["other_legs"]["delivery_carrier"] = self._delivery_carrier.name
            self._main_request["other_legs"]["delivery_carrier_id"] = self._delivery_carrier.code
            self._delivery_request = copy.deepcopy(self._base)
            self._delivery_request["is_pickup"] = False
            self._delivery_request["carrier_id"] = self._delivery_carrier.code
            self._delivery_request["carrier_email"] = self._delivery_carrier.email
            self._delivery_request["service_code"] = getkey(self._service, "delivery.service_code", '')
            self._delivery_request["origin"] = copy.deepcopy(self._gobox_request["destination"])
            self._delivery_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
            self._delivery_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])

        self._main_request["carrier_id"] = self._main_carrier.code
        self._main_request["carrier_email"] = self._main_carrier.email
        self._main_request["carrier_name"] = self._main_carrier.name
        self._main_request["service_code"] = getkey(self._service, "service_code", '')
        self._main_request["service_name"] = sailing.get_name_display()
        self._main_request["origin"] = mid_origin
        self._main_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
        self._main_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])

    def _send_requests(self):
        shipment = Shipment()

        pickup_leg, main_leg, delivery_leg = shipment.one_step_save(
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

        # Pickup Leg
        if self._pickup_request:
            pickup_greenlet = self._create_greenlets(order_number=pickup_leg.leg_id, request=self._pickup_request)

        # Delivery Leg
        if self._delivery_request:
            delivery_greenlet = self._create_greenlets(order_number=delivery_leg.leg_id, request=self._delivery_request)

        self._main_request["dg_service"] = self._dg_main
        self._main_request["order_number"] = main_leg.leg_id

        main_greenlet = self._create_greenlets(order_number=main_leg.leg_id, request=self._main_request)
        markup = self._sub_account.markup
        exchange_rate = self._get_exchange_rate()

        if self._pickup_request:
            pickup_data = self._get_data_from_greenlet(
                leg=pickup_leg,
                greenlet=pickup_greenlet,
                markup=markup
            )

            pickup_leg = shipment.leg_shipment.get(type="P")
            pickup_data['pickup_requested'] = self._pickup_request['is_pickup']
            # Hold first leg for sealift, untell we can confirmation FTL/ LTL Booking
            pickup_leg.update_leg(update_params=pickup_data, exchange_rate=exchange_rate, on_hold=True)

            self._response['pickup_leg'] = pickup_data
        else:
            pickup_leg = None
            self._response['pickup_leg'] = None

        self._response['pickup_leg_dropoff_location'] = self._main_request["origin"]

        # Delivery Leg
        if self._delivery_request:
            delivery_data = self._get_data_from_greenlet(
                leg=delivery_leg,
                greenlet=delivery_greenlet,
                markup=markup
            )

            delivery_leg = shipment.leg_shipment.get(type="D")
            delivery_data['pickup_requested'] = self._delivery_request['is_pickup']
            delivery_leg.update_leg(update_params=delivery_data, exchange_rate=exchange_rate, on_hold=True)
            self._response['delivery_leg'] = delivery_data
        else:
            delivery_leg = None
            self._response['delivery_leg'] = None

        self._response['delivery_leg_pickup_location'] = self._main_request['destination']

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

        main_data['pickup_requested'] = self._main_request['is_pickup']
        self._response['main_leg'] = main_data
        main_leg.update_leg(update_params=main_data, exchange_rate=exchange_rate)

        self._response['shipment_id'] = shipment.shipment_id

        if self._user.username == "GoBox":
            self._response["markup"] = markup.default_percentage
            self._response['main_leg']["markup"] = main_leg.markup

            if pickup_leg:
                self._response['pickup_leg']["markup"] = pickup_leg.markup

            if delivery_leg:
                self._response['delivery_leg']["markup"] = delivery_leg.markup

        shipment.update()

        return shipment

    def ship(self) -> tuple:
        """

            :return: Shipping Response Dict
        """
        self._main_carrier = self._gobox_request["objects"]["m_carrier"]
        self._pickup_carrier = self._gobox_request["objects"].get("p_carrier", None)
        self._delivery_carrier = self._gobox_request["objects"].get("d_carrier", None)

        self._setup()

        if self._gobox_request["is_dangerous_shipment"]:
            self._dg_main = DangerousGoodsGround(self._main_request)

        shipment = self._send_requests()

        return self._response, shipment
