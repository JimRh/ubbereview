from typing import Union

from api.apis.carriers.canada_post.soap_objects.customs import Customs
from api.apis.carriers.canada_post.soap_objects.options import Options
from api.apis.carriers.canada_post.soap_objects.parcel_chracteristics import (
    ParcelCharacteristics,
)
from api.apis.carriers.canada_post.soap_objects.preferences import Preferences
from api.apis.carriers.canada_post.soap_objects.print_preferences import (
    PrintPreferences,
)
from api.apis.carriers.canada_post.soap_objects.references import References
from api.apis.carriers.canada_post.soap_objects.sender import Sender
from api.apis.carriers.canada_post.soap_objects.settlement_info import SettlementInfo
from api.apis.carriers.canada_post.soap_objects.ship_destination import ShipDestination
from api.apis.carriers.canada_post.soap_objects.soap_obj import SOAPObj


class DeliverySpec(SOAPObj):
    def __init__(self, world_request: dict, order_number: str) -> None:
        self._world_request = world_request
        self._order_number = order_number
        self._options = Options(world_request).data()

        # if world_request["Destination"]["Country"] != "CA":
        #     self._is_international = True
        # else:
        #     self._is_international = False
        self._is_international = False

    # Override
    def _clean(self) -> None:
        pass

    # Override
    def data(self) -> Union[list, dict]:
        data = {
            "service-code": self._world_request["service_code"],
            "sender": Sender(self._world_request["origin"]).data(),
            "parcel-characteristics": ParcelCharacteristics(
                self._world_request["packages"][0]
            ).data(),
            "print-preferences": PrintPreferences().data(),
            "preferences": Preferences().data(),
            "references": References(
                self._order_number, self._world_request.get("awb")
            ).data(),
            "settlement-info": SettlementInfo(self._world_request).data(),
        }

        if self._options:
            data["options"] = self._options

        if self._is_international:
            data["destination"] = ShipDestination(
                self._world_request["destination"], True
            ).data()
            data["customs"] = Customs().data()
        else:
            data["destination"] = ShipDestination(
                self._world_request["destination"]
            ).data()

        return data
