"""
    Title: DayRoss Ship
    Description: This file will contain functions related to Day Ross and Sameday Shipping..
    Created: July 13, 2020
    Author: Carmichael
    Edited By:
    Edited Date:

    Notes:
        - Service Level
            GX is for making a shipment without creating a pickup
            GL is for making a shipment and creating a pickup at the same time

"""

import base64
from decimal import Decimal, InvalidOperation

from django.db import connection
from lxml import etree
from zeep.exceptions import Fault

from api.apis.carriers.day_ross_v2.endpoints.day_ross_api_v2 import DayRossAPI
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException, ViewException
from api.globals.carriers import DAY_N_ROSS
from api.globals.project import DOCUMENT_TYPE_SHIPPING_LABEL
from api.utilities.date_utility import DateUtility


class DayRossShip(DayRossAPI):
    _surcharges = [
        "FTAXLT",
        "FSC-A",
        "FSC-G",
        "AIS",
        "NAVCN5",
        "DANGER",
        "PRESPU",
        "PRESDL",
        "PROTEC",
        "APTFGT",
        "INSDLY",
        "DANGEROUS",
        "APPTPU",
        "APPT",
        "HEAT",
        "HAZARD",
    ]

    def __init__(self, ubbe_request: dict) -> None:
        super(DayRossShip, self).__init__(ubbe_request=ubbe_request)
        self._response = {}

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    def _build_request(self):
        """
        Format main body for shipment request.
        :return:
        """

        ready_time, close_time = self._create_pickup()
        special_instructions = self._ubbe_request.get("special_instructions", "")
        if "awb" in self._ubbe_request:
            air = self._ubbe_request["air_carrier"]
            awb = self._ubbe_request["awb"]

            special_instructions += (
                f"\nPlease reference {air} Airway Bill: {awb} on arrival."
            )

        data = {
            "ShipperAddress": self._create_address(self._origin),
            "ConsigneeAddress": self._create_address(self._destination),
            "BillToAccount": self._account_number,
            "Items": self._create_items(self._ubbe_request["packages"]),
            "ServiceLevel": self._ubbe_request["service_code"],
            "ShipmentType": self._shipment_type,
            "PaymentType": self._payment_type,
            "MeasurementSystem": self._measurement_system,
            "Division": self._division,
            "SpecialInstructions": special_instructions,
            "ReferenceNumbers": self._create_references(),
            "ExpiryDate": self._expiry_date,
            "ReadyTime": ready_time,
            "ClosingTime": close_time,
            "ServiceType": self._service_type,
        }

        try:
            if self._carrier_id == DAY_N_ROSS:
                self._create_options_day_ross(data=data)
            else:
                self._create_options_same_day(data=data)
        except ViewException as e:
            raise ShipException(
                {
                    "api.error.dr.ship": f"Ship Request Fail: Please contact support. {e.message}"
                }
            )

        return self._dr_ns0.Shipment(**data)

    def _process_documents(self, labels) -> None:
        """
        Get documents for shipment.
        :param labels: base64 pdf document of cargo labels and BOL, day ross branded
        :return:
        """
        if labels:
            self._response["documents"].append(
                {
                    "document": base64.b64encode(labels).decode("ascii"),
                    "type": DOCUMENT_TYPE_SHIPPING_LABEL,
                }
            )

        if self._ubbe_request.get("is_dangerous_goods", False) and self._dg_service:
            self._ubbe_request["tracking_number"] = self._response["tracking_number"]
            self._response["documents"].append(self._dg_service.generate_documents())

    def _format_response(self, response: dict) -> None:
        """
        Format day ross response into ubbe response.
        :param response: SOAP response
        :return:
        """

        try:
            data = response["Charges"]["ServiceLevels"][0]
        except KeyError:
            raise ShipException({"api.error.dr.ship": "D&R api not active"})

        if data["TransitTime"]:
            transit = int(data["TransitTime"])
        else:
            transit = -1

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request.get("pickup")
        ).get_estimated_delivery(
            transit=transit,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        self._response = {
            "carrier_id": self._ubbe_request["carrier_id"],
            "carrier_name": self._name,
            "service_code": data["ServiceLevelCode"],
            "service_name": str(data["Description"]).title(),
            "surcharges": [],
            "surcharges_cost": Decimal("0.00"),
            "freight": Decimal("0.00"),
            "taxes": Decimal("0.00"),
            "tax_percent": Decimal("0.00"),
            "total": Decimal(str(data["TotalAmount"])),
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
            "tracking_number": response["Probill"],
            "documents": [],
        }

        for charge in data["ShipmentCharges"]["ShipmentCharge"]:
            charge_code = charge["ChargeCode"]

            if charge_code == "TARIFF" or charge_code == "TRFAMT":
                self._response["freight"] = Decimal(str(charge["Amount"]))

            elif charge_code in self._surcharges:
                amount = Decimal(str(charge["Amount"]))

                try:
                    percent = Decimal(str(charge["AdditionalInfo"]))
                except (KeyError, TypeError, InvalidOperation):
                    percent = Decimal("0.00")

                self._response["surcharges"].append(
                    {
                        "name": charge["Description"],
                        "cost": amount,
                        "percentage": percent,
                    }
                )

                self._response["surcharges_cost"] += amount
            elif charge_code in [
                "ONHST",
                "HST",
                "GST",
                "PST",
                "NSHST",
                "NLHST",
                "NBHST",
            ]:
                self._response["taxes"] = Decimal(str(charge["Amount"]))

        sub_total = self._response["total"] - self._response["taxes"]
        tax_percent = round(
            self._response["taxes"] / Decimal(str(sub_total)) * Decimal("100"), 0
        )
        purchase_surcharge = self.get_purchase_surcharge()
        surcharges = self._response["surcharges_cost"] + purchase_surcharge

        tax = (self._response["freight"] + surcharges) * (
            tax_percent.quantize(self._sig_fig) / 100
        )
        new_total = self._response["freight"] + surcharges + tax

        self._response["surcharges"].append(
            {
                "name": "Purchased Transportation Surcharge",
                "cost": purchase_surcharge,
                "percentage": Decimal("0.0"),
            }
        )

        self._response["taxes"] = tax.quantize(self._sig_fig)
        self._response["tax_percent"] = tax_percent
        self._response["surcharges_cost"] = surcharges
        self._response["total"] = new_total
        self._process_documents(response["Labels"])

    def _post(self, request):
        """
        Send shipment Request to Day Ross to ship.
        :param request: SOAP shipment request
        :return: response
        """

        try:
            response = self._dr_client.service.CreateShipment4(
                division=self._division,
                emailAddress=self._username,
                password=self._password,
                shipment=request,
                language="EN",
                labelFormat="PDF",
            )
        except Fault as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_ship.py line: 161",
                message=str(
                    {"api.error.dr.ship": "Zeep Failure: {}".format(e.message)}
                ),
            )
            CeleryLogger().l_info.delay(
                location="day_ross_ship.py line: 161",
                message="Day and Ross Ship request data: {}".format(
                    etree.tounicode(self._dr_history.last_sent["envelope"])
                ),
            )
            CeleryLogger().l_info.delay(
                location="day_ross_ship.py line: 161",
                message="Day and Ross Ship response data: {}".format(
                    etree.tounicode(self._dr_history.last_received["envelope"])
                ),
            )

            raise ShipException(
                {"api.error.dr.ship": "Could not ship D&R, request error"}
            )

        return response

    def ship(self) -> dict:
        """
        Ship Day Ross shipment.
        :return: ubbe carrier shipment response
        """

        try:
            request = self._build_request()
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_ship.py line: 273",
                message=str(
                    {"api.error.dr.ship": "Ship Request Fail: {}".format(str(e))}
                ),
            )
            raise ShipException(
                {"api.error.dr.ship": "Ship Request Fail: Please contact support."}
            )

        try:
            response = self._post(request=request)
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_ship.py line: 273",
                message=str(
                    {"api.error.dr.ship": "Shipping Failure: {}".format(str(e))}
                ),
            )

            CeleryLogger().l_info.delay(
                location="day_ross_ship.py line: 161",
                message="Day and Ross Ship request data: {}".format(str(request)),
            )

            raise ShipException(
                {"api.error.dr.ship": "Shipping Failure: Please contact support."}
            )

        try:
            self._format_response(response=response)
        except Exception as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_ship.py line: 284",
                message=str(
                    {"api.error.dr.ship": "Ship Format Error:: {}".format(str(e))}
                ),
            )
            raise ShipException(
                {"api.error.dr.ship": "Ship Format Error: Please contact support."}
            )

        return self._response
