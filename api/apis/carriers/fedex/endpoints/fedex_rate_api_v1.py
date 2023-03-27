import copy
import datetime
from decimal import Decimal

from django.db import connection
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from api.apis.carriers.fedex.globals.globals import TRANSIT_TIME
from api.apis.carriers.fedex.globals.services import RATE_SERVICE, RATE_HISTORY
from api.apis.carriers.fedex.soap_objects.rate.fedex_rate_request import (
    FedExRateRequest,
)
from api.apis.carriers.fedex.utility.utility import FedexUtility
from api.background_tasks.logger import CeleryLogger
from api.globals.carriers import FEDEX


class FedExRate:
    def __init__(self, gobox_request: dict):
        self.gobox_request = copy.deepcopy(gobox_request)

        self.sub_account = gobox_request["objects"]["sub_account"]
        self.carrier_account = gobox_request["objects"]["carrier_accounts"][FEDEX][
            "account"
        ]
        self.carrier = gobox_request["objects"]["carrier_accounts"][FEDEX]["carrier"]
        self.gobox_request[
            "account_number"
        ] = self.carrier_account.account_number.decrypt()
        self.gobox_request[
            "meter_number"
        ] = self.carrier_account.contract_number.decrypt()
        self.gobox_request["key"] = self.carrier_account.api_key.decrypt()
        self.gobox_request["password"] = self.carrier_account.password.decrypt()

    @staticmethod
    def process_rates(fedex_rates: list) -> list:
        rates = []

        for fedex_rate in fedex_rates:
            service = fedex_rate["ServiceDescription"]
            rated_details = fedex_rate["RatedShipmentDetails"]
            delivery_timestamp = fedex_rate["DeliveryTimestamp"]
            code = service.get("Code", "")
            description = service.get("Description", "")

            if description == "2Day":
                description = "Fedex 2 Day"
            elif description == "FedEx Economy":
                description = "Fedex Express Saver"

            try:
                delivery_date = delivery_timestamp.replace(microsecond=0).isoformat()
            except Exception:
                delivery_date = (
                    datetime.datetime(year=1, month=1, day=1)
                    .replace(microsecond=0, second=0, minute=0, hour=0)
                    .isoformat()
                )

            for rated_detail in rated_details:
                shipment_rate_details = rated_detail["ShipmentRateDetail"]
                rate_type = shipment_rate_details["RateType"]

                if len(rated_details) > 1:
                    if rate_type != "PREFERRED_ACCOUNT_SHIPMENT":
                        continue

                total_tax = shipment_rate_details["TotalTaxes"]["Amount"]
                net_freight = shipment_rate_details["TotalNetFedExCharge"]["Amount"]
                tax_percent = (total_tax / net_freight).quantize(
                    Decimal("0.01")
                ) * Decimal("100")

                returned_transit_time = fedex_rate["MaximumTransitTime"]

                if not returned_transit_time:
                    returned_transit_time = fedex_rate["TransitTime"]
                    if not returned_transit_time:
                        returned_transit_time = "UNKNOWN"

                transit_time = TRANSIT_TIME.get(returned_transit_time, -1)

                if transit_time == -1 and delivery_timestamp:
                    transit_time = (
                        delivery_timestamp.date() - datetime.datetime.today().date()
                    ).days

                rate = {
                    "carrier_id": FEDEX,
                    "carrier_name": "FedEx",
                    "service_code": code,
                    "service_name": description,
                    "freight": shipment_rate_details["TotalNetFreight"]["Amount"],
                    "surcharge": shipment_rate_details["TotalSurcharges"]["Amount"],
                    "tax": total_tax,
                    "tax_percent": tax_percent,
                    "total": shipment_rate_details["TotalNetCharge"]["Amount"],
                    "transit_days": transit_time,
                    "delivery_date": delivery_date,
                }
                rates.append(rate)
        return rates

    def rate(self):
        try:
            rate_data = FedExRateRequest(self.gobox_request).data
            rates = serialize_object(RATE_SERVICE.getRates(**rate_data))
            # from lxml import etree
            # LOGGER.debug(etree.tounicode(RATE_HISTORY.last_sent['envelope'], pretty_print=True))
            # LOGGER.debug(etree.tounicode(RATE_HISTORY.last_received['envelope'], pretty_print=True))
            successful, messages = FedexUtility.successful_response(response=rates)
        except Fault:
            from lxml import etree

            CeleryLogger().l_debug.delay(
                location="fedex_rate_api.py line: 102",
                message=etree.tounicode(
                    RATE_HISTORY.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_debug.delay(
                location="fedex_rate_api.py line: 107",
                message=etree.tounicode(
                    RATE_HISTORY.last_received["envelope"], pretty_print=True
                ),
            )

            return []

        if not successful:
            connection.close()
            return []

        connection.close()
        return self.process_rates(rates["RateReplyDetails"])
