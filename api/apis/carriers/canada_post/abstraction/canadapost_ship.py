import base64
import datetime
import io
import string
from decimal import Decimal
from typing import Any, Dict, List

import gevent
from PyPDF2 import PdfFileWriter, PdfFileReader
from django.db import connection
from zeep.exceptions import Fault

from api.apis.carriers.canada_post.abstraction.canadapost_api import CanadaPostAPI
from api.apis.carriers.canada_post.abstraction.canadapost_validate_service import (
    CanadaPostValidateRate,
)
from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.globals.util import Endpoints
from api.apis.carriers.canada_post.soap_objects.shipment import Shipment
from api.apis.carriers.canada_post.soap_objects.shipment_refund_request import (
    ShipmentRefundRequest,
)
from api.apis.carriers.canada_post.soap_objects.transmit_set import TransmitSet
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException
from api.globals.carriers import CAN_POST
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
    LOGGER,
)

# TODO: Extract out transmit, artifact, manifest
from api.utilities.date_utility import DateUtility


class CanadaPostShip(CanadaPostAPI):
    _default_max_retries = 5
    _option_codes = {
        "COD": "Collect on delivery",
        "COV": "Insurance coverage",
        "CYL": "Mailing tube",
        "DC": "Delivery confirmation",
        "PA18": "Proof of age 18 years",
        "PA19": "Proof of age 19 years",
        "SO": "Signature option",
        "UP": "Unpackaged",
    }
    _surcharge_codes = {
        "AUTDISC": "Automation discount",
        "FUELSC": "Fuel surcharge",
        "NCNTGST": "Non-contiguous state fee (applies to Priority Worldwide products sent to Alaska and Hawaii)",
        "V1DISC": "Solutions for Small Business savings",
        "PROMODISC": "Promotional discount (if the promo code is invalid or expired, the discount amount will show as "
        "zero under adjustment-amount)",
        "PLATFMDISC": "Discount for using an e-commerce platform",
        "NEWREGDISC": "Discount for joining the Developer Program",
        "ORIGSC": "Service area adjustment (at origin)",
        "DESTSC": "Service area adjustment (at destination)",
        "PURFEE": "Fee charged for using a label before it was paid for (i.e., before performing Transmit Shipments)",
        "SAADJ": "Service area adjustment (rate adjustment up or down for specific source and destination postal code "
        "combinations)",
    }

    def __init__(self, world_request: dict) -> None:
        super(CanadaPostShip, self).__init__(world_request)
        self._world_request["origin"]["postal_code"] = self._process_postal_code(
            self._world_request["origin"]["postal_code"]
        )
        self._world_request["destination"]["postal_code"] = self._process_postal_code(
            self._world_request["destination"]["postal_code"]
        )
        self._number_of_packages = sum(
            package.get("quantity", 1) for package in self._world_request["packages"]
        )

        self._order_number = ""
        self._artifacts = []
        self._prices = {}
        self._manifest_numbers = []

        self.carrier_account = world_request["objects"]["carrier_accounts"][CAN_POST][
            "account"
        ]

        self.endpoints = Endpoints(self.carrier_account)
        self._world_request["_carrier_account"] = self.carrier_account

    @staticmethod
    def _process_postal_code(postal_code: str) -> str:
        postal_code = postal_code.upper()

        for char in string.punctuation:
            postal_code = postal_code.replace(char, "")
        return postal_code

    def _refund_shipment(self, shipment_id: str) -> dict:
        if not 1 <= len(shipment_id) < 33:
            return {"success": False}

        try:
            response = self.endpoints.SHIPMENT_SERVICE.RequestShipmentRefund(
                **{
                    "mailed-by": self.carrier_account.account_number.decrypt(),
                    "shipment-id": shipment_id,
                    "shipment-refund-request": ShipmentRefundRequest(
                        "developer@bbex.com"
                    ).data(),
                }
            )
        except Fault as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_ship line: 103",
                message=str(
                    {"api.error.canada_post.Ship": "Zeep Failure: {}".format(e.message)}
                ),
            )

            raise ShipException(
                {"api.error.canada_post.Refund": "Error refunding shipment"}
            )
        except CanadaPostAPIException as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_ship line: 110",
                message=str({"api.error.canada_post.Ship": e.message}),
            )
            raise ShipException(
                {"api.error.canada_post.Refund": "Error refunding shipment"}
            )

        if response["shipment-refund-request-info"]:
            return {"success": True}
        messages = [
            "CanadaPost Errcode: {} - {}".format(
                message["code"], str(message["description"])
            )
            for message in response["messages"]["message"]
        ]
        raise ShipException(messages)

    def _transmit_shipments(self, order_number: str, postal_code: str) -> list:
        try:
            resp = self.endpoints.MANIFEST_SERVICE.TransmitShipments(
                **{
                    "mailed-by": self.carrier_account.account_number.decrypt(),
                    "transmit-set": TransmitSet(order_number, postal_code).data(),
                }
            )
        except Fault as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_ship line: 131",
                message=str(
                    {"api.error.canada_post.Ship": "Zeep Failure: {}".format(e.message)}
                ),
            )
            raise ShipException(
                {"api.error.canada_post.Ship": "Error transmitting shipment"}
            )

        if resp["messages"] is not None:
            CeleryLogger().l_critical.delay(
                location="canadapost_ship line: 138",
                message=str({"api.error.canada_post.Ship": resp["messages"]}),
            )
            raise ShipException(
                {"api.error.canada_post.Ship": "Shipment transmission error"}
            )
        manifest_numbers = []

        for manifest in resp["manifests"]["manifest-id"]:
            manifest_numbers.append(manifest)
        gevent.sleep(0.5)
        return manifest_numbers

    def _void_shipment(self, shipment_id: str) -> dict:
        if not 1 <= len(shipment_id) < 33:
            return {"success": False}

        try:
            response = self.endpoints.SHIPMENT_SERVICE.VoidShipment(
                **{
                    "mailed-by": self.carrier_account.account_number.decrypt(),
                    "shipment-id": shipment_id,
                }
            )
        except Fault as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_ship line: 160",
                message=str(
                    {"api.error.canada_post.Ship": "Zeep Failure: {}".format(e.message)}
                ),
            )
            raise ShipException(
                {"api.error.canada_post.Void": "Error voiding shipment"}
            )

        if response["void-shipment-success"]:
            return {"success": True}
        messages = [
            "CanadaPost Errcode: {} - {}".format(
                message["code"], str(message["description"])
            )
            for message in response["messages"]["message"]
        ]
        raise ShipException(messages)

    def _get_manifest(self, manifest_number) -> None:
        max_retries = self._default_max_retries

        while max_retries:
            try:
                resp = self.endpoints.MANIFEST_SERVICE.GetManifestArtifactId(
                    **{
                        "mailed-by": self.carrier_account.account_number.decrypt(),
                        "manifest-id": manifest_number,
                    }
                )
            except Fault as e:
                CeleryLogger().l_critical.delay(
                    location="canadapost_ship line: 184",
                    message=str(
                        {
                            "api.error.canada_post.Ship": "Zeep Failure: {}".format(
                                e.message
                            )
                        }
                    ),
                )
                raise ShipException(
                    {
                        "api.error.canada_post.Ship": "Error getting getting manifest from CanadaPost"
                    }
                )

            if resp["messages"] is not None:
                descriptions = [
                    str(m["description"]).lower() for m in resp["messages"]["message"]
                ]
                codes = [str(m["code"]).lower() for m in resp["messages"]["message"]]

                if "rejected by slm monitor" in descriptions:
                    max_retries -= 1
                    gevent.sleep(0.5)
                elif "8511" in codes:
                    max_retries -= 1
                elif "9153" in codes:
                    gevent.sleep(0.5)
                else:
                    raise ShipException(
                        {"api.error.canada_post.Ship": "Could not get manifest"}
                    )
            else:
                self._get_shipment_artifact(
                    resp["manifest"]["artifact-id"], DOCUMENT_TYPE_BILL_OF_LADING
                )
                return None
        raise ShipException(
            {"api.error.canada_post.Ship": "Max get manifest retries exceeded"}
        )

    def _get_shipment_artifact(self, artifact_id, document_type: int) -> None:
        max_retries = self._default_max_retries

        while max_retries:
            try:
                artifact_response = self.endpoints.ARTIFACT_SERVICE.GetArtifact(
                    **{"artifact-id": artifact_id}
                )
            except Fault as e:
                CeleryLogger().l_critical.delay(
                    location="canadapost_ship line: 217",
                    message=str(
                        {
                            "api.error.canada_post.Ship": "Zeep Failure: {}".format(
                                e.message
                            )
                        }
                    ),
                )
                raise ShipException(
                    {"api.error.canada_post.Ship": "Error getting shipment artifact(s)"}
                )

            if artifact_response["messages"] is not None:
                descriptions = [
                    str(m["description"]).lower()
                    for m in artifact_response["messages"]["message"]
                ]
                codes = [
                    str(m["code"]).lower()
                    for m in artifact_response["messages"]["message"]
                ]

                if "rejected by slm monitor" in descriptions:
                    max_retries -= 1
                    gevent.sleep(0.5)
                elif "8511" in codes:
                    max_retries -= 1
                else:
                    raise ShipException(
                        {"api.error.canada_post.Ship": "Error getting artifact(s)"}
                    )
            else:
                self._artifacts.append(
                    (document_type, artifact_response["artifact-data"]["image"])
                )
                return None
        raise ShipException(
            {"api.error.canada_post.Ship": "Max get artifact(s) retries exceeded"}
        )

    def _get_shipment_price(self, shipment_id: str, package_id: int) -> Dict[str, Any]:
        if self._prices.get(package_id):
            return self._prices[package_id]
        max_retries = self._default_max_retries

        while max_retries:
            try:
                price = self.endpoints.SHIPMENT_SERVICE.GetShipmentPrice(
                    **{
                        "mailed-by": self.carrier_account.account_number.decrypt(),
                        "shipment-id": shipment_id,
                    }
                )
            except Fault as e:
                CeleryLogger().l_critical.delay(
                    location="canadapost_ship line: 254",
                    message=str(
                        {
                            "api.error.canada_post.Ship": "Zeep Failure: {}".format(
                                e.message
                            )
                        }
                    ),
                )
                raise ShipException(
                    {
                        "api.error.canada_post.Ship": "Error getting shipment package cost details"
                    }
                )

            if price["messages"] is not None:
                descriptions = [
                    str(m["description"]).lower() for m in price["messages"]["message"]
                ]
                codes = [str(m["code"]).lower() for m in price["messages"]["message"]]

                if "rejected by slm monitor" in descriptions:
                    max_retries -= 1
                    gevent.sleep(0.5)
                elif "8511" in codes:
                    max_retries -= 1
                else:
                    raise ShipException(
                        {"api.error.canada_post.Ship": "Could not get cost of shipping"}
                    )
            else:
                self._prices[package_id] = price["shipment-price"]

                return price["shipment-price"]
        raise ShipException(
            {"api.error.canada_post.Ship": "Max get shipment cost retries exceeded"}
        )

    def _process_artifacts(self) -> List[Dict[str, Any]]:
        inputs = {}

        for artifact in self._artifacts:
            key = artifact[0]
            val = inputs.get(key, [])
            val.append(io.BytesIO(base64.b64decode(artifact[1])))
            inputs[key] = val
        ret = []

        for key, value in inputs.items():
            output = io.BytesIO()
            writer = PdfFileWriter()

            for reader in map(PdfFileReader, value):
                for n in range(reader.getNumPages()):
                    writer.addPage(reader.getPage(n))
            if not value:
                writer.addBlankPage(4 * 72, 6 * 72)
            writer.write(output)
            output.seek(0)
            encoded = base64.b64encode(output.read())

            for i in value:
                i.close()
            output.close()
            ret.append({"document": encoded.decode("ascii"), "type": key})
        return ret

    def _process_responses(self, response, shipment_price) -> dict:
        info = response["shipment-info"]

        if not shipment_price["service-standard"]["expected-transmit-time"]:
            estimated_delivery_date, transit_days = DateUtility(
                pickup=self._world_request.get("pickup", {})
            ).get_estimated_delivery(
                transit=self._default_transit,
                province=self._world_request["origin"]["province"],
                country=self._world_request["origin"]["country"],
            )
        else:
            transit_days = shipment_price["service-standard"]["expected-transmit-time"]
            delivery_date = shipment_price["service-standard"]["expected-delivery-date"]
            estimated_delivery_date = datetime.datetime.combine(
                delivery_date, datetime.datetime.min.time()
            ).isoformat()

        ret = {
            "total": Decimal(str(shipment_price["due-amount"])),
            "taxes": Decimal(str(shipment_price["gst-amount"]))
            + Decimal(str(shipment_price["pst-amount"]))
            + Decimal(str(shipment_price["hst-amount"])),
            "po_number": info["po-number"],
            "tracking_number": info["tracking-pin"],
            "id": info["shipment-id"],
            "transit_days": transit_days,
            "delivery_date": estimated_delivery_date,
        }

        surcharges = []
        surcharges_cost = Decimal("0.00")

        for option in shipment_price["priced-options"]["priced-option"]:
            cost = Decimal(str(option["option-price"]))

            if cost:
                surcharges_cost += cost

                surcharges.append(
                    {
                        "name": self._option_codes[option["option-code"]],
                        "cost": cost,
                        "percentage": Decimal("0.00"),
                    }
                )

        for surcharge in shipment_price["adjustments"]["adjustment"]:
            cost = Decimal(str(surcharge["adjustment-amount"]))

            if cost:
                surcharges_cost += cost

                surcharges.append(
                    {
                        "name": self._surcharge_codes[surcharge["adjustment-code"]],
                        "cost": cost,
                        "percentage": Decimal("0.00"),
                    }
                )

        ret["surcharges"] = surcharges
        ret["surcharges_cost"] = surcharges_cost

        for artifact in info["artifacts"]["artifact"]:
            self._get_shipment_artifact(
                artifact["artifact-id"], DOCUMENT_TYPE_SHIPPING_LABEL
            )
        return ret

    def _ship(self, package_id: int) -> dict:
        """
        --- NOTE ---
        Canada Post requests that shipments are made serially, not in parallel
        This module has been written to ship packages of a shipment sequentially
        """
        max_retries = self._default_max_retries

        while max_retries:
            try:
                shipment = self.endpoints.SHIPMENT_SERVICE.CreateShipment(
                    **{
                        "mailed-by": self.carrier_account.account_number.decrypt(),
                        "shipment": Shipment(
                            self._world_request, self._order_number
                        ).data(),
                    }
                )
            except Fault as e:
                CeleryLogger().l_critical.delay(
                    location="canadapost_ship line: 369",
                    message=str(
                        {
                            "api.error.canada_post.Ship": "Zeep Failure: {}".format(
                                e.message
                            )
                        }
                    ),
                )
                raise ShipException(
                    {
                        "api.error.canada_post.Ship": "Error sending shipment information to CanadaPost"
                    }
                )

            if shipment["messages"] is not None:
                descriptions = [
                    str(m["description"]).lower()
                    for m in shipment["messages"]["message"]
                ]
                codes = [
                    str(m["code"]).lower() for m in shipment["messages"]["message"]
                ]

                if "rejected by slm monitor" in descriptions:
                    max_retries -= 1
                    gevent.sleep(0.5)
                elif "8511" in codes:
                    max_retries -= 1
                else:
                    raise ShipException(
                        {
                            "api.error.canada_post.Ship": "Could not ship package. "
                            "Error codes: {} {}".format(codes, descriptions)
                        }
                    )
            else:
                price = self._get_shipment_price(
                    shipment["shipment-info"]["shipment-id"], package_id
                )

                return self._process_responses(shipment, price)
        raise ShipException({"api.error.canada_post.Ship": "Max ship retries exceeded"})

    def ship(self) -> Dict[str, Any]:
        # Temporary
        if self._world_request["destination"]["country"] != "CA":
            connection.close()
            raise ShipException(
                {
                    "api.not_implemented.canada_post.ship": "Canada Post international shipping not supported"
                }
            )

        if self._world_request.get("carrier_options", []):
            connection.close()
            raise ShipException(
                {"api.forbidden.canada_post.ship": "Carrier options not supported"}
            )

        self._order_number = self._world_request["order_number"]
        origin = self._world_request["origin"]
        valid_service, service_name = CanadaPostValidateRate(
            self._world_request
        ).is_valid()

        if not valid_service:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="canadapost_ship line: 414",
                message="Canada Post shipping invalid shipment: {}".format(
                    service_name
                ),
            )
            raise ShipException(
                {
                    "api.error.canada_post.Ship": 'The service "'
                    + service_name
                    + '" cannot be serviced as requested'
                }
            )
        shipments = []

        if not self._world_request.get("do_not_ship", False):
            # --- NOTE ---
            # Canada Post requests that shipments are made serially, not in parallel
            # This module has been written to ship packages of a shipment sequentially

            for i, package in enumerate(self._world_request["packages"]):
                for _ in range(package.get("quantity", 1)):
                    try:
                        # Create Shipment(s) + Get Shipment Price + Get Artifact(s)
                        single_shipment = self._ship(i)
                    except ShipException:
                        connection.close()
                        for shipment in shipments:
                            self._void_shipment(shipment["id"])
                        raise
                    shipments.append(single_shipment)

        total = Decimal("0.00")
        taxes = Decimal("0.00")
        surcharges_cost = Decimal("0.00")
        surcharges = []
        po_numbers = []
        tracking_numbers = []
        shipment_ids = []
        transit = -1
        delivery_date = None

        for shipment in shipments:
            total += shipment["total"]
            taxes += shipment["taxes"]
            surcharges_cost += shipment["surcharges_cost"]
            surcharges.extend(shipment["surcharges"])
            po_number = shipment["po_number"]
            transit = shipment["transit_days"]
            delivery_date = shipment["delivery_date"]

            if po_number:
                po_numbers.append(po_number)
            tracking_numbers.append(shipment["tracking_number"])
            shipment_ids.append(shipment["id"])

        # Transmit
        try:
            manifest_numbers = self._transmit_shipments(
                self._order_number, origin["postal_code"]
            )
        except ShipException:
            connection.close()
            raise

        # Get Manifest(s) + Final Get Artifact(s)
        manifest_threads = [
            gevent.Greenlet.spawn(self._get_manifest, manifest_number)
            for manifest_number in manifest_numbers
        ]

        gevent.joinall(manifest_threads)

        try:
            for manifest_thread in manifest_threads:
                manifest_thread.get()
        except ShipException:
            connection.close()
            error_messages = {
                "api.error.canada_post.Ship": "Error transmitting shipment to Canada Post"
            }

            if not self._world_request.get("do_not_pickup", False):
                for shipment_id in shipment_ids:
                    try:
                        self._refund_shipment(shipment_id)
                    except ShipException:
                        error_messages.update(
                            {
                                "api.error.canada_post.Ship.Transmit.Ship.Exception": "Failed to refund shipments after transmit"
                            }
                        )
            raise ShipException(error_messages)

        if not delivery_date:
            delivery_date = (
                datetime.datetime(year=1, month=1, day=1)
                .replace(microsecond=0)
                .isoformat()
            )

        return_value = {
            "total": total,
            "freight": total - taxes - surcharges_cost,
            "taxes": taxes,
            "surcharges": surcharges,
            "surcharges_cost": surcharges_cost,
            "tax_percent": (taxes / (total - taxes) * 100).quantize(Decimal(".01")),
            "carrier_id": CAN_POST,
            "service_code": self._world_request["service_code"],
            "carrier_name": "Canada Post",
            "service_name": service_name,
            "transit_days": transit,
            "delivery_date": delivery_date,
            "pickup_id": "",
            "tracking_number": ",".join(tracking_numbers),
            "documents": self._process_artifacts(),
        }

        if self._world_request.get("is_dangerous_goods", False):
            self._world_request["tracking_number"] = return_value["tracking_number"]
            dg_ground = self._world_request["dg_service"]

            return_value["documents"].append(dg_ground.generate_documents())

        connection.close()
        return return_value

    # Override
    def _format_response(self) -> None:
        pass

    # Override
    def _post(self) -> None:
        pass
