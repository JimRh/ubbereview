import copy

from django.db import connection

from api.apis.multi_modal.ship.ship_common import ShipCommon
from api.apis.services.airbase.airbase import FindAirbase
from api.apis.services.dangerous_goods.dangerous_goods_air import DangerousGoodsAir
from api.exceptions.project import ViewException, ShipException, DangerousGoodsException
from api.globals.carriers import CAN_NORTH, WESTJET, AIR_NORTH, CARGO_JET, AIR_INUIT
from api.globals.project import getkey
from api.models import NorthernPDAddress, Shipment, ProBillNumber
from api.utilities.carriers import CarrierUtility


class AirShip(ShipCommon):
    """
        ubbe Multi Model Shipping - Determines what mode to ship. IE: Ground, Air, or Sealift
    """

    def __init__(self, gobox_request: dict) -> None:
        super(AirShip, self).__init__(gobox_request=gobox_request)

    @staticmethod
    def _get_awb(carrier_id: int) -> tuple:
        awb = ProBillNumber.objects.filter(carrier__code=carrier_id, available=True).first()

        if not awb:
            connection.close()
            raise ShipException({"api.error.waybill": "No available WestJet air waybills"})

        awb_num = awb.probill_number
        awb.available = False
        awb.save()

        if carrier_id == WESTJET:
            awb_num = '838-' + awb_num

        return awb_num

    def _check_canadian_location(self, key: str, errors: dict):

        city = getkey(self._gobox_request, key + '.city', '')

        if not NorthernPDAddress.objects.filter(city_name=city).exists():
            errors['service.' + key + '.invalid_location'] = 'Carrier cannot perform pickup in {}'.format(city)

    def _check_service(self):
        """
            Check carriers, specially CN (Check if carrier can do Pickup or Delivery).
        """
        errors = {}

        self._main_carrier = self._gobox_request["objects"]["m_carrier"]
        self._pickup_carrier = self._gobox_request["objects"].get("p_carrier", None)
        self._delivery_carrier = self._gobox_request["objects"].get("d_carrier", None)

        if self._pickup_carrier and self._pickup_carrier.code == CAN_NORTH:
            self._check_canadian_location(key="origin", errors=errors)

        if self._delivery_carrier and self._delivery_carrier.code == CAN_NORTH:
            self._check_canadian_location(key="destination", errors=errors)

        if errors:
            connection.close()
            raise ViewException(errors)

    def _get_airbases(self):
        carrier_id = self._main_carrier.code

        mid_origin, mid_destination = FindAirbase().get_airbase_by_code(
            carrier_id=carrier_id,
            origin_code=self._service["origin_base"],
            destination_code=self._service["destination_base"]
        )

        if not mid_origin or not mid_destination:
            connection.close()
            raise ViewException({
                "api.ship.airbase.error": "No airbases near origin/destination for carrier: {}".format(carrier_id)
            })

        self._mid_origin = mid_origin
        self._mid_destination = mid_destination

    def _setup(self):
        """
            Setup shipping request for air shipments.
        """
        is_pickup = False
        is_delivery = False

        self._main_request = copy.deepcopy(self._base)
        self._main_request["other_legs"] = {}

        # Attempt to get Airbases
        self._get_airbases()

        original_mid_o = copy.deepcopy(self._mid_origin)
        original_mid_d = copy.deepcopy(self._mid_destination)

        # Update origin and destination
        self._setup_address(address=self._mid_origin, key="origin")
        self._setup_address(address=self._mid_destination, key="destination")

        if self._pickup_carrier:
            is_pickup = True
            self._setup_address(address=original_mid_o, key="destination")

            original_mid_o["name"] = original_mid_o["company_name"]
            original_mid_o["company_name"] = f" CO {self._main_carrier.name}"

            self._main_request["other_legs"]["pickup_carrier"] = self._pickup_carrier
            self._pickup_request = copy.deepcopy(self._base)
            self._pickup_request["carrier_id"] = self._pickup_carrier.code
            self._pickup_request["carrier_email"] = self._pickup_carrier.email
            self._pickup_request["is_pickup"] = self._pickup_carrier.code == CAN_NORTH
            self._pickup_request["service_code"] = getkey(self._service, "pickup.service_code", '')

            self._pickup_request["destination"] = original_mid_o

            self._pickup_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
            self._pickup_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])

        if self._delivery_carrier:
            is_delivery = True

            self._main_request["other_legs"]["delivery_carrier"] = self._delivery_carrier
            self._delivery_request = copy.deepcopy(self._base)
            self._delivery_request["is_pickup"] = False
            self._delivery_request["carrier_id"] = self._delivery_carrier.code
            self._delivery_request["carrier_email"] = self._delivery_carrier.email
            self._delivery_request["service_code"] = getkey(self._service, "delivery.service_code", '')

            self._delivery_request["origin"] = self._mid_destination

            self._delivery_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
            self._delivery_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])

        self._main_request["carrier_id"] = self._main_carrier.code
        self._main_request["carrier_email"] = self._main_carrier.email
        self._main_request["carrier_name"] = self._main_carrier.name
        self._main_request["service_code"] = getkey(self._service, "service_code", '')
        self._main_request["origin"] = self._mid_origin
        self._main_request["destination"] = self._mid_destination
        self._main_request["ultimate_origin"] = copy.deepcopy(self._gobox_request["origin"])
        self._main_request["ultimate_destination"] = copy.deepcopy(self._gobox_request["destination"])
        self._main_request["is_pickup"] = is_pickup
        self._main_request["is_delivery"] = is_delivery

    def _send_requests(self):
        shipment = Shipment()
        markup = self._sub_account.markup
        exchange_rate = self._get_exchange_rate()

        self._response['pickup_leg'] = None
        self._response['delivery_leg'] = None

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

        if self._main_request["is_dangerous_goods"]:
            try:
                self._dg_main.clean()

                if self._dg_main.is_shipment_dg:
                    self._dg_main.parse()
            except DangerousGoodsException as e:
                connection.close()
                raise ShipException(e.message)

        # Get carrier AWB Number and add it to requests
        if self._main_carrier.code in [WESTJET, AIR_NORTH, AIR_INUIT]:
            awb_num = self._get_awb(carrier_id=self._main_carrier.code)
            self._main_request['awb'] = awb_num

        # Main Leg
        self._main_request["dg_service"] = self._dg_main
        self._main_request['order_number'] = main_leg.leg_id
        main_carrier = CarrierUtility().get_ship_api(data=self._main_request)

        try:
            main_response = main_carrier.ship(order_number=main_leg.leg_id)
        except ShipException as e:
            if self._main_carrier.code == WESTJET:
                ProBillNumber.objects.filter(carrier__code=WESTJET, probill_number=awb_num).update(available=True)
            shipment.delete()
            connection.close()
            raise ShipException({"api.error.greenlet.data": f"Unable to get data: {e.message}"})

        multiplier = self._get_multiplier(markup=markup.default_percentage, c_markup=main_leg.markup)
        self._apply_markup_to_rate(main_response, multiplier)
        main_response['pickup_requested'] = self._main_request['is_pickup']
        main_leg.update_leg(update_params=main_response, exchange_rate=exchange_rate)

        if self._pickup_request:
            self._pickup_request['awb'] = main_leg.tracking_identifier
            self._pickup_request['air_carrier'] = self._main_carrier.name
        if self._delivery_request:
            self._delivery_request['awb'] = main_leg.tracking_identifier
            self._delivery_request['air_carrier'] = self._main_carrier.name

        # Pickup Leg
        if self._pickup_request:
            pickup_greenlet = self._create_greenlets(order_number=pickup_leg.leg_id, request=self._pickup_request)

        # Delivery Leg
        if self._delivery_request:
            delivery_greenlet = self._create_greenlets(order_number=delivery_leg.leg_id, request=self._delivery_request)

        if self._pickup_request:
            pickup_data = self._get_data_from_greenlet(
                leg=pickup_leg,
                greenlet=pickup_greenlet,
                markup=markup,
            )

            pickup_data['pickup_requested'] = self._pickup_request['is_pickup']
            pickup_leg.update_leg(update_params=pickup_data, exchange_rate=exchange_rate)

            self._response['pickup_leg'] = pickup_data
        self._response['pickup_leg_dropoff_location'] = self._main_request["origin"]

        # Delivery Leg
        if self._delivery_request:
            delivery_data = self._get_data_from_greenlet(
                leg=delivery_leg,
                greenlet=delivery_greenlet,
                markup=markup,
            )

            delivery_data['pickup_requested'] = self._delivery_request['is_pickup']
            carrier_id = delivery_data['carrier_id']

            if carrier_id == CAN_NORTH:
                delivery_data['pickup_requested'] = True
                delivery_leg.update_leg(update_params=delivery_data, exchange_rate=exchange_rate)
            else:
                delivery_leg.update_leg(update_params=delivery_data, exchange_rate=exchange_rate, on_hold=True)

            self._response['delivery_leg'] = delivery_data
        self._response['delivery_leg_pickup_location'] = self._main_request['destination']

        self._response['main_leg'] = main_response
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

        self._check_service()
        self._setup()

        if self._gobox_request["is_dangerous_goods"]:
            self._dg_main = DangerousGoodsAir(self._main_request)

        shipment = self._send_requests()

        return self._response, shipment
