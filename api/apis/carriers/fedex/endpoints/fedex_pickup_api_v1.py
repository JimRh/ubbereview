import copy
import datetime

from lxml import etree
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from api.apis.carriers.fedex.globals.globals import TRANSIT_TIME
from api.apis.carriers.fedex.globals.services import (
    PICKUP_SERVICE,
    PICKUP_HISTORY,
    SERVICE_SERVICE,
)
from api.apis.carriers.fedex.soap_objects.pickup.create_pickup_request import (
    CreatePickupRequest,
)
from api.apis.carriers.fedex.soap_objects.pickup_commitment.create_pickup_commitment import (
    CreatePickupCommitmentRequest,
)
from api.apis.carriers.fedex.utility.utility import FedexUtility
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import PickupException
from api.globals.carriers import FEDEX
from api.utilities.date_utility import DateUtility


class FedExPickup:
    def __init__(self, gobox_request: dict):
        self._gobox_request = copy.deepcopy(gobox_request)
        self.carrier_account = gobox_request["objects"]["carrier_accounts"][FEDEX][
            "account"
        ]
        self.carrier = gobox_request["objects"]["carrier_accounts"][FEDEX]["carrier"]
        self._gobox_request[
            "account_number"
        ] = self.carrier_account.account_number.decrypt()
        self._gobox_request[
            "meter_number"
        ] = self.carrier_account.contract_number.decrypt()
        self._gobox_request["key"] = self.carrier_account.api_key.decrypt()
        self._gobox_request["password"] = self.carrier_account.password.decrypt()

    def pickup(self) -> dict:
        pickup_data = CreatePickupRequest(self._gobox_request).data

        try:
            pickup_response = serialize_object(
                PICKUP_SERVICE.createPickup(**pickup_data)
            )
            successful, messages = FedexUtility.successful_response(pickup_response)
        except Fault:
            messages = []
            CeleryLogger().l_critical.delay(
                location="fedex_pickup_api.py line: 18",
                message=etree.tounicode(
                    PICKUP_HISTORY.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_critical.delay(
                location="fedex_pickup_api.py line: 18",
                message=etree.tounicode(
                    PICKUP_HISTORY.last_received["envelope"], pretty_print=True
                ),
            )
            successful = False

        if len(messages) == 1 and messages[0]["Code"] == "5148":
            return {
                "pickup_id": "",
            }
        if not successful:
            raise PickupException(
                {"fedex.pickup.error": "Error creating pickup request"}
            )

        pickup_location = (
            pickup_response["Location"] if pickup_response["Location"] else ""
        )
        pickup_confirmation = (
            pickup_response["PickupConfirmationNumber"]
            if pickup_response["PickupConfirmationNumber"]
            else ""
        )

        pickup_number = "{}{}".format(
            pickup_location,
            pickup_confirmation.rstrip(),
        )

        ret = {
            "pickup_id": pickup_number,
            "pickup_message": "Booked",
            "pickup_status": "Success",
        }

        ret.update(self._pickup_availability())

        if ret["transit_days"] and int(ret["transit_days"]) != -1:
            ret["transit_days"] = int(ret["transit_days"])
        else:
            ret["transit_days"] = -1

        estimated_delivery_date, transit = DateUtility(
            pickup=self._gobox_request.get("pickup")
        ).get_estimated_delivery(
            transit=ret["transit_days"],
            country=self._gobox_request["origin"]["country"],
            province=self._gobox_request["origin"]["province"],
        )

        ret["transit_days"] = transit
        ret["delivery_date"] = estimated_delivery_date

        return ret

    def _pickup_availability(self):
        pickup_data = CreatePickupCommitmentRequest(
            pickup_request=self._gobox_request
        ).data

        try:
            pickup_response = serialize_object(
                SERVICE_SERVICE.serviceAvailability(**pickup_data)
            )

            successful, messages = FedexUtility.successful_response(pickup_response)
        except Fault as e:
            CeleryLogger().l_critical.delay(
                location="fedex_pickup_api.py line: 72",
                message=etree.tounicode(
                    SERVICE_SERVICE.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_critical.delay(
                location="fedex_pickup_api.py line: 72",
                message=etree.tounicode(
                    SERVICE_SERVICE.last_received["envelope"], pretty_print=True
                ),
            )
            raise PickupException(
                {"fedex.pickup.error": "Error getting pickup commitment"}
            )

        if not successful:
            raise PickupException(
                {"fedex.pickup.error": "Error getting pickup commitment"}
            )

        options = pickup_response["Options"]

        if options:
            delivery_date = options[0]["DeliveryDate"]
            transit_time = options[0]["TransitTime"]

            if transit_time:
                transit_time = TRANSIT_TIME[transit_time]
            else:
                if delivery_date:
                    delivery_datetime = datetime.datetime.combine(
                        delivery_date, datetime.datetime.min.time()
                    )
                    date_now = datetime.datetime.now()
                    delta = delivery_datetime - date_now
                    days = delta.days

                    transit_time = days + 1

            return {
                "transit_days": transit_time if transit_time else -1,
            }

        return {"transit_days": -1}
