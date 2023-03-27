import base64
import copy
import io
from decimal import Decimal

import gevent
from PyPDF2 import PdfFileWriter, PdfFileReader
from django.db import connection
from lxml import etree
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from api.apis.carriers.fedex.globals.services import SHIP_SERVICE, SHIP_HISTORY
from api.apis.carriers.fedex.soap_objects.ship.delete_shipment_request import (
    DeleteShipmentRequest,
)
from api.apis.carriers.fedex.soap_objects.ship.process_shipment_request import (
    ProcessShipmentRequest,
)
from api.apis.carriers.fedex.utility.utility import FedexUtility
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException
from api.globals.carriers import FEDEX
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)


# TODO: CLEAN UP SHIPPING


class FedExShip:
    def __init__(self, gobox_request: dict):
        carrier_account = gobox_request["objects"]["carrier_accounts"][FEDEX]["account"]

        gobox_request["account_number"] = carrier_account.account_number.decrypt()
        gobox_request["meter_number"] = carrier_account.contract_number.decrypt()
        gobox_request["key"] = carrier_account.api_key.decrypt()
        gobox_request["password"] = carrier_account.password.decrypt()
        # gobox_request['unmodified_packages'] = copy.deepcopy(gobox_request['packages'])

        # Get Commodities for international multi package shipment
        if gobox_request["is_international"]:
            gobox_request["unmodified_packages"] = self.international_commodities(
                copy.deepcopy(gobox_request["packages"])
            )
            gobox_request["packages"] = copy.deepcopy(
                gobox_request["unmodified_packages"]
            )

        self.gobox_request = copy.deepcopy(gobox_request)
        self.gobox_pickup_request = copy.deepcopy(gobox_request)

    @staticmethod
    def international_commodities(packages):
        commodities = []
        for package in packages:
            for commodity in package["commodities"]:
                commodities.append(commodity)

        for package in packages:
            package["commodities"] = commodities
        return packages

    @staticmethod
    def _process_labels(labels: list, key=DOCUMENT_TYPE_SHIPPING_LABEL) -> list:
        inputs = {}
        ret = []

        for label in labels:
            val = inputs.get(key, [])
            val.append(io.BytesIO(label))
            inputs[key] = val

        for doctype, value in inputs.items():
            output = io.BytesIO()
            writer = PdfFileWriter()

            for reader in (PdfFileReader(val, strict=False) for val in value):
                for n in range(reader.getNumPages()):
                    writer.addPage(reader.getPage(n))

            if not value:
                writer.addBlankPage(4 * 72, 6 * 72)

            writer.write(output)
            output.seek(0)
            encoded = base64.b64encode(output.read())
            # try:
            #     file_content = base64.b64decode(encoded.decode('ascii'))
            #     with open("/home/graham/Documents/q" + str(randint(0, 10000)) + ".pdf", "wb") as f:
            #         f.write(file_content)
            # except Exception as e:
            #     print(str(e))

            for i in value:
                i.close()
            output.close()
            ret.append({"document": encoded.decode("ascii"), "type": doctype})
        return ret

    def _process_response(self, ship_response: dict):
        surcharge_list = []

        if ship_response:
            completed_shipment = ship_response["CompletedShipmentDetail"]
            master_tracking = completed_shipment["MasterTrackingId"]["TrackingNumber"]
            label_parts = [
                part["Image"]
                for part in completed_shipment["CompletedPackageDetails"][0]["Label"][
                    "Parts"
                ]
            ]
            description = completed_shipment["ServiceDescription"]["Description"]

            if completed_shipment["ShipmentRating"]:
                rate = completed_shipment["ShipmentRating"]["ShipmentRateDetails"][-1]
                total_tax = rate["TotalTaxes"]["Amount"]
                net_freight = rate["TotalNetFedExCharge"]["Amount"]
                tax_percent = (total_tax / net_freight).quantize(
                    Decimal("0.01")
                ) * Decimal("100")
                total_freight = rate["TotalNetFreight"]["Amount"]
                total = rate["TotalNetCharge"]["Amount"]
                total_surcharges = rate["TotalSurcharges"]["Amount"]
                fuel_surcharge_percent = rate["FuelSurchargePercent"]

                for surcharge in rate["Surcharges"]:
                    if surcharge["SurchargeType"] == "FUEL":
                        surcharge_list.append(
                            {
                                "name": "Fuel Surcharge",
                                "cost": surcharge["Amount"]["Amount"],
                                "percentage": fuel_surcharge_percent,
                            }
                        )
                    else:
                        surcharge_list.append(
                            {
                                "name": surcharge["Description"],
                                "cost": surcharge["Amount"]["Amount"],
                                "percentage": Decimal("0.00"),
                            }
                        )
            else:
                total_tax = Decimal("0")
                tax_percent = Decimal("0")
                total_freight = Decimal("0")
                total = Decimal("0")
                total_surcharges = Decimal("0")

            labels_threads = [gevent.Greenlet.spawn(self._process_labels, label_parts)]
            labels = []  # self._process_labels(label_parts)

            if completed_shipment.get("ShipmentDocuments"):
                ci_document_parts = [
                    part["Image"]
                    for part in completed_shipment["ShipmentDocuments"][0]["Parts"]
                ]
                ci_document_parts *= completed_shipment["ShipmentDocuments"][0].get(
                    "CopiesToPrint", 3
                )
                labels_threads.append(
                    gevent.Greenlet.spawn(
                        self._process_labels,
                        ci_document_parts,
                        DOCUMENT_TYPE_COMMERCIAL_INVOICE,
                    )
                )

            gevent.joinall(labels_threads)

            for thread in labels_threads:
                labels.append(*thread.get())

            ship_return = {
                "carrier_id": FEDEX,
                "carrier_name": "FedEx",
                "service_code": self.gobox_request["service_code"],
                "service_name": description,
                "total": total,
                "freight": total_freight,
                "taxes": total_tax,
                "surcharges": surcharge_list,
                "surcharges_cost": total_surcharges,
                "tax_percent": tax_percent,
                "transit_days": -1,
                "tracking_number": master_tracking,
                "documents": labels,
            }

            return ship_return

        return {}

    def _split_packages(self) -> list:
        packages = [
            package
            for package in self.gobox_request["packages"]
            for _ in range(package["quantity"])
        ]
        for package in packages:
            package["quantity"] = 1
        return packages

    def _ship_package(
        self,
        package: dict,
        master_tracking=None,
        sequence: int = None,
        num_packages: int = None,
    ) -> dict:
        self.gobox_request["packages"] = [package]

        ship_data = ProcessShipmentRequest(
            self.gobox_request,
            master_tracking=master_tracking,
            sequence=sequence,
            num_packages=num_packages,
        ).data

        try:
            ship_response = serialize_object(SHIP_SERVICE.processShipment(**ship_data))
            # LOGGER.debug(etree.tounicode(SHIP_HISTORY.last_sent['envelope'], pretty_print=True))
            # LOGGER.debug(etree.tounicode(SHIP_HISTORY.last_received['envelope'], pretty_print=True))
            successful, messages = FedexUtility.successful_response(ship_response)
        except Fault:
            # pylint: disable=I1101
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 165",
                message=etree.tounicode(
                    SHIP_HISTORY.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 165",
                message=etree.tounicode(
                    SHIP_HISTORY.last_received["envelope"], pretty_print=True
                ),
            )
            # pylint: enable=I1101
            connection.close()
            raise ShipException({"FedEx.Ship": "Error shipping"})

        if not successful:
            connection.close()
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 178",
                message=etree.tounicode(
                    SHIP_HISTORY.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 178",
                message=etree.tounicode(
                    SHIP_HISTORY.last_received["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 178", message=str(messages)
            )
            raise ShipException({"FedEx.Ship": "Error shipping"})

        return self._process_response(ship_response)

    @staticmethod
    def cancel_shipment(tracking_number: str):
        cancel_data = DeleteShipmentRequest(tracking_number).data
        try:
            cancel_response = serialize_object(
                SHIP_SERVICE.deleteShipment(**cancel_data)
            )
            # LOGGER.debug(etree.tounicode(SHIP_HISTORY.last_sent['envelope'], pretty_print=True))
            # LOGGER.debug(etree.tounicode(SHIP_HISTORY.last_received['envelope'], pretty_print=True))
            successful, messages = FedexUtility.successful_response(cancel_response)
        except Fault:
            # pylint: disable=I1101
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 192",
                message=etree.tounicode(
                    SHIP_HISTORY.last_sent["envelope"], pretty_print=True
                ),
            )
            CeleryLogger().l_debug.delay(
                location="fedex_ship_api.py line: 192",
                message=etree.tounicode(
                    SHIP_HISTORY.last_received["envelope"], pretty_print=True
                ),
            )
            # pylint: enable=I1101

    def ship(self) -> dict:
        master_tracking = None
        if not self.gobox_request.get("do_not_ship"):
            packages = self._split_packages()
            number_of_packages = len(packages)

            first_package = packages.pop(0)
            sequence = 1
            first_resp = self._ship_package(
                first_package, sequence=sequence, num_packages=number_of_packages
            )

            master_tracking = first_resp["tracking_number"]

            responses = [first_resp]
            package_threads = []

            for package in packages:
                sequence += 1

                package_threads.append(
                    gevent.Greenlet.spawn(
                        self._ship_package,
                        package,
                        master_tracking,
                        sequence,
                        num_packages=number_of_packages,
                    )
                )

            gevent.joinall(package_threads)

            for package_thread in package_threads:
                responses.append(package_thread.get())

            # Merge Packages documents and responses
            pre_merge_documents = {}
            pre_merge_surcharges = {}
            total = Decimal("0.0")
            freight = Decimal("0.0")
            taxes = Decimal("0.0")
            surcharges = Decimal("0.0")

            for response in responses:
                total += response["total"]
                freight += response["freight"]
                taxes += response["taxes"]
                surcharges += response["surcharges_cost"]

                for document in response["documents"]:
                    doctype = document["type"]
                    document = document["document"]

                    if not pre_merge_documents.get(doctype):
                        pre_merge_documents[doctype] = []

                    pre_merge_documents[doctype].append(base64.b64decode(document))

                for surcharge in response["surcharges"]:
                    if not pre_merge_surcharges.get(surcharge["name"]):
                        pre_merge_surcharges[surcharge["name"]] = []

                        pre_merge_surcharges[surcharge["name"]].append(surcharge)

            documents = []
            for doctype, docs in pre_merge_documents.items():
                documents.append(*self._process_labels(labels=docs, key=doctype))

            surcharges_list = []
            for name, charge_list in pre_merge_surcharges.items():
                amount = Decimal("0.0")
                percentage = Decimal("0.0")
                for charge in charge_list:
                    amount += charge["cost"]
                    percentage = charge["percentage"]

                surcharges_list.append(
                    {"name": name, "cost": amount, "percentage": percentage}
                )

            ship_response = {
                "total": total,
                "freight": freight,
                "taxes": taxes,
                "surcharges": surcharges_list,
                "surcharges_cost": surcharges,
                "tax_percent": first_resp["tax_percent"],
                "carrier_id": FEDEX,
                "service_code": self.gobox_request["service_code"],
                "carrier_name": "FedEx",
                "service_name": first_resp["service_name"],
                "transit_days": first_resp["transit_days"],
                "tracking_number": master_tracking,
                "documents": documents,
            }
        else:
            ship_response = {
                "documents": [],
                "carrier_id": FEDEX,
                "carrier_name": "FedEx",
                "tracking_number": "",
                "total": Decimal("0.00"),
                "freight": Decimal("0.00"),
                "service_code": self.gobox_request["service_code"],
                "service_name": "",
                "surcharges": Decimal("0.00"),
                "taxes": Decimal("0.00"),
                "tax_percent": Decimal("0"),
                "transit_days": -1,
            }

        connection.close()
        return ship_response
