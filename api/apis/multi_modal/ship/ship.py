import copy


from api.apis.multi_modal.ship.air_ahip import AirShip
from api.apis.multi_modal.ship.ground_ship import GroundShip
from api.apis.multi_modal.ship.mc_ground_ship import MultiCarrierGroundShip
from api.apis.multi_modal.ship.sealift_ship import SealiftShip
from api.globals.carriers import UBBE_INTERLINE


class MultiModelShip:
    """
        ubbe Multi Model Shipping - Determines what mode to ship. IE: Ground, Air, or Sealift
    """
    _air = "AI"
    _sealift = "SE"

    def __init__(self, gobox_request: dict) -> None:
        self._gobox_request = copy.deepcopy(gobox_request)
        self._appointment_delivery = 1
        self._service = self._gobox_request["service"]
        self._user = self._gobox_request["objects"]["user"]
        self._main_carrier = self._gobox_request["objects"]["m_carrier"]
        self._response = {}

    def _determine_shipping_mode(self) -> None:
        """
            Determine what mode to process the shipment request
        """

        if self._main_carrier.code == UBBE_INTERLINE:
            self._response, self.shipment = MultiCarrierGroundShip(gobox_request=self._gobox_request).ship()
        elif self._main_carrier.mode == self._air:
            self._response, self.shipment = AirShip(gobox_request=self._gobox_request).ship()
        elif self._main_carrier.mode == self._sealift:
            # Sealift Mode
            self._response, self.shipment = SealiftShip(gobox_request=self._gobox_request).ship()
        else:
            # Ground Mode
            self._response, self.shipment = GroundShip(gobox_request=self._gobox_request).ship()

    def ship(self) -> tuple:
        self._gobox_request['api_client_email'] = self._user.email
        self._determine_shipping_mode()

        if self.shipment.subaccount.is_account_id:
            self._response["account_id"] = self.shipment.account_id
            self._response["packages"] = list(self.shipment.package_shipment.values("package_id", "package_account_id"))

        return self._response, self.shipment
