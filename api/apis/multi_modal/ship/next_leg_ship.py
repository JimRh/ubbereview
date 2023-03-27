import copy

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch

from api.apis.services.dangerous_goods.dangerous_goods_ground import DangerousGoodsGround
from api.exceptions.project import ShipNextException, ViewException
from api.globals.carriers import RATE_SHEET_CARRIERS, SEALIFT_CARRIERS
from api.models import Shipment, Leg, SubAccount, CarrierAccount
from api.process_json.process_ship import ProcessShipJson
from api.utilities.carriers import CarrierUtility


# TODO NEXT LEG DG?

class ShipNextLeg:

    def __init__(self, shipment_id: str, user: User, booking_id: str):
        self._shipment_id = shipment_id
        self._booking_id = booking_id
        self._shipment = None
        self._leg = None
        self._user = user
        self._response = {}

    def _validate_shipment_id(self):
        try:
            self._shipment = Shipment.objects.select_related(
                "sender",
                "receiver",
                "subaccount"
            ).prefetch_related(
                "package_shipment",
                Prefetch(
                    "leg_shipment", queryset=Leg.objects.select_related(
                        "carrier",
                        "origin__province__country",
                        "destination__province__country"
                    ).prefetch_related(
                        "surcharge_leg"
                    )
                )
            ).get(shipment_id=self._shipment_id)
        except ObjectDoesNotExist:
            raise ShipNextException({'next_leg.shipment_id.error': "Shipment id '" + self._shipment_id + "' does not exist"})

    def _create_base_request(self):
        self._base = {
            "order_number": self._user.email,
            "api_client_email": self._user.email,
            "sub_account": self._get_sub_account(),
            "reference_one": self._shipment.reference_one,
            "reference_two": self._shipment.reference_two,
            "booking_bumber": self._shipment.booking_number,
            "tracking_number": self._leg.tracking_identifier,
            "pickup": {
                "date": self._shipment.requested_pickup_time.strftime("%Y-%m-%d"),
                "start_time": self._shipment.requested_pickup_time.strftime("%H:%M"),
                "end_time": self._shipment.requested_pickup_close_time.strftime("%H:%M")
            },
            "packages": self._get_packages(),
            "commodities": self._get_commodities(),
            "is_food": self._shipment.is_food,
            "leg_id": self._leg.leg_id,
            "is_dangerous_shipment": self._shipment.is_dangerous_good
        }

    def _get_commodities(self):
        return [commodity.next_leg_json() for commodity in self._shipment.commodity_shipment.all()]

    def _get_packages(self):
        return [package.to_json() for package in self._shipment.package_shipment.all()]

    def _get_sub_account(self):
        return SubAccount.objects.select_related(
                "markup",
                "client_account"
            ).prefetch_related(
                Prefetch(
                    "carrieraccount_subaccount", queryset=CarrierAccount.objects.select_related(
                        "carrier",
                        'api_key',
                        'username',
                        'password',
                        'account_number',
                        'contract_number',
                    )
                )
            ).get(subaccount_number=str(self._shipment.subaccount.subaccount_number))

    def _ship_api(self):
        try:
            api = CarrierUtility.get_ship_api(data=self._base)
        except ViewException as err:
            raise ShipNextException(err.message)

        try:
            response = api.ship(order_number=self._leg.leg_id)
        except ViewException as err:
            raise ShipNextException(err.message)

        self._leg.on_hold = False
        self._leg.pickup_identifier = response["api_pickup_id"]
        self._leg.carrier_pickup_identifier = response["carrier_pickup_id"]
        self._leg.save()

        self._response = {
            "leg_id": self._leg.leg_id,
            "tracking_number": self._leg.tracking_identifier,
            "carrier_pickup_id": self._leg.carrier_pickup_identifier,
            # "Documents": documents
        }

    def _ship_rate_sheet(self):

        try:
            api = CarrierUtility.get_ship_api(data=self._base)
        except ViewException as err:
            raise ShipNextException(err.message)

        try:
            response = api.ship()
        except ViewException as err:
            raise ShipNextException(err.message)

        self._leg.on_hold = False
        self._leg.pickup_identifier = response["tracking_number"]
        self._leg.carrier_pickup_identifier = response["tracking_number"]
        self._leg.save()

        self._response = {
            "leg_id": self._leg.leg_id,
            "tracking_number": self._leg.pickup_identifier,
            "documents": response["documents"]
        }

    def _update_base_request(self):
        if self._leg.type == "P":
            o_contact = self._shipment.sender
            d_contact = self._shipment.sender
        elif self._leg.type == "M":
            o_contact = self._shipment.sender
            d_contact = self._shipment.receiver
        elif self._leg.type == "D":
            o_contact = self._shipment.receiver
            d_contact = self._shipment.receiver
        else:
            raise ShipNextException({'next_leg.leg_type.error': "'leg_type' is not defined."})

        self._base.update({
            "order_number": self._leg.leg_id,
            "service": {
                "carrier_id": self._leg.carrier.code,
                "service_code": self._leg.service_code,
            },
            "carrier_id": self._leg.carrier.code,
            "service_code": self._leg.service_code,
            "service_name": self._leg.service_name,
            "origin": self._leg.origin.next_leg_json(contact=o_contact),
            "destination": self._leg.destination.next_leg_json(contact=d_contact),
            "pickup": self._leg.create_pickup()
        })

    def ship_next_leg(self):
        self._validate_shipment_id()
        self._leg = self._shipment.leg_shipment.filter(on_hold=True).first()

        if not self._leg:
            raise ShipNextException({'next_leg.shipment_id.error': "'shipment_id' all legs have been shipped."})

        self._shipment.booking_number = self._booking_id
        self._shipment.save()

        self._create_base_request()
        self._update_base_request()

        try:
            ProcessShipJson(gobox_request=self._base, user=self._user).clean()
        except ViewException as e:
            raise ShipNextException(e.message)

        carrier_accounts, carriers = CarrierUtility().get_carrier_accounts_ship(
            sub_account=self._shipment.subaccount,
            gobox_request=self._base
        )

        self._base["objects"] = {
            "sub_account": self._shipment.subaccount,
            "user": self._user,
            "carrier_accounts": carrier_accounts,
            "sealift_list": CarrierUtility().get_sealift()
        }

        if self._base["is_dangerous_shipment"]:
            self._base["is_dg_shipment"] = True
            self._base["dg_service"] = DangerousGoodsGround(copy.deepcopy(self._base))

        if self._base["carrier_id"] in RATE_SHEET_CARRIERS or self._base["carrier_id"] in SEALIFT_CARRIERS:
            self._ship_rate_sheet()
        else:
            self._ship_api()

        return self._response
