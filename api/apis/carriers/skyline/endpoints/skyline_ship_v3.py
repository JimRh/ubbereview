import base64
import copy
from datetime import date
from decimal import Decimal
from typing import Dict, Union

import gevent
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from api.apis.carriers.skyline.exceptions.exceptions import SkylineShipError
from api.apis.carriers.skyline.services.interlines import GetInterlineID
from api.apis.carriers.skyline.services.pickup_delivery_cost import PickupDeliveryCost
from api.apis.carriers.skyline.services.pickup_delivery_email import PickupDeliveryEmail
from api.apis.carriers.skyline.services.transit_time import Transit
from api.apis.carriers.skyline.endpoints.skyline_api_v3 import SkylineAPI
from api.apis.services.dangerous_goods.dangerous_goods_air import DangerousGoodsAir
from api.background_tasks.logger import CeleryLogger
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import ShipException, RequestError
from api.globals.carriers import CAN_NORTH
from api.globals.project import (
    getkey,
    DEFAULT_TIMEOUT_SECONDS,
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
)
from api.models import API, CityNameAlias
from api.utilities.date_utility import DateUtility


class SkylineShip(SkylineAPI):
    """
    Class will handle all details about a Skyline ship request.
    """

    def __init__(self, gobox_request: dict, order_number: str = ""):
        super(SkylineShip, self).__init__(gobox_request)
        self._order_number = order_number
        self._skyline_request = {}
        self._is_cn_pickup = False
        self._is_cn_delivery = False
        self._skyline_response = {}
        self._response = {}

    @staticmethod
    def _download_document(
        document_type: int, awb: str, api_key: str, url: str
    ) -> Dict[str, Union[int, str]]:
        """
        Make Skyline document call for each of the documents, which includes Cargo labels and airway bill.
        """
        data = {"API_Key": api_key, "WaybillNumber": awb[-8:]}
        try:
            response = requests.post(url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException:
            connection.close()
            raise RequestError()

        try:
            response.raise_for_status()
            document = response.content
        except (ValueError, requests.RequestException):
            connection.close()
            raise RequestError(response, data)

        encoded = base64.b64encode(document)
        ret = {"document": encoded.decode("ascii"), "type": document_type}
        connection.close()
        return ret

    @staticmethod
    def _process_surcharges(surcharge_data) -> tuple:
        """
        Process skyline surcharges and format into GoBox surcharges.
        """
        surcharges = []
        surcharges_cost = Decimal("0.00")

        for surcharge in surcharge_data:
            cost = Decimal(str(surcharge["Amount"]))

            if cost:
                surcharges_cost += cost

                if surcharge["Percentage"] is not None:
                    percentage = Decimal(str(surcharge["Percentage"]))
                else:
                    percentage = Decimal("0.00")

                surcharges.append(
                    {"name": surcharge["Name"], "cost": cost, "percentage": percentage}
                )

        return surcharges, surcharges_cost

    def _do_not_ship(self):
        """
        Skyline do not ship function for Pickup and Delivery service.
        """

        estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
            transit=1,
            country=self._gobox_request["origin"]["country"],
            province=self._gobox_request["origin"]["province"],
        )

        return {
            "documents": [],
            "carrier_id": CAN_NORTH,
            "carrier_name": "Canadian North",
            "tracking_number": "",
            "total": Decimal("0.00"),
            "freight": Decimal("0.00"),
            "carrier_pickup_id": "",
            "api_pickup_id": "",
            "service_code": self._gobox_request["service_code"],
            "service_name": "",
            "surcharges": [],
            "surcharges_cost": Decimal("0.00"),
            "taxes": Decimal("0.00"),
            "tax_percent": Decimal("0.00"),
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
        }

    def _build_address(self, address: dict, key: str) -> None:
        """
        Build skyline address format for ship request and check city name alias.
        """
        city = CityNameAlias.check_alias(
            alias=address["city"],
            province_code=address["province"],
            country_code=address["country"],
            carrier_id=CAN_NORTH,
        )

        self._skyline_request[key] = {
            "Name": address["company_name"],
            "Country": address["country"],
            "City": city,
            "PostalCode": address["postal_code"],
            "EmailAddress": "customerservice@ubbe.com",
            "Address": address["address"],
            "Province": address["province"],
            "Telephone": address["phone"],
            "Attention": address["name"],
        }

    def _build_packages(self):
        """
        Copy processed packages for the ship request and add Rate Priority ID and Nature of Good ID to each
        package.
        """
        copied_packages = copy.deepcopy(self._processed_packages)
        service_code = self._gobox_request["service_code"]
        rate_priority_code = ""

        for pack in copied_packages:
            nog_id = pack["NogId"]

            # pri and general nog
            if int(self._gobox_request["service_code"]) == 2 and int(nog_id) == 302:
                # pri and PRIORITY CARGO
                nog_id = 36

            try:
                nog = self._nature_of_goods.get(
                    rate_priority_id=service_code, nog_id=nog_id
                )
            except ObjectDoesNotExist as e:
                raise SkylineShipError("No NOG Found. data {}".format(e))

            pack["RatePriorityId"] = service_code
            pack["NatureOfGoodsId"] = nog.nog_id
            rate_priority_code = nog.rate_priority_code

        self._skyline_request["Packages"] = copied_packages
        self._gobox_request["rp"] = rate_priority_code
        self._gobox_request["rp_id"] = service_code

    def _build_shipping_carriers(self):
        """
        Build any skyline pickup or delivery data and calculate the charge for them. The function also
        builds any additional handling instructions.
        """
        instruction_fields = []
        other_charges = []
        other_legs = self._gobox_request.get("other_legs")

        if self._gobox_request.get("special_instructions"):
            instruction_fields.append(self._gobox_request["special_instructions"])

        origin_city = getkey(self._gobox_request, "ultimate_origin.city", "")
        destination_city = getkey(self._gobox_request, "ultimate_destination.city", "")

        p_and_d = PickupDeliveryCost(
            is_pickup=self._is_pickup,
            is_delivery=self._is_delivery,
            total_weight=self._total_weight,
            total_dim=self._total_dim,
            origin_city=origin_city,
            delivery_city=destination_city,
        )

        # Determine if Canadian North pickup leg exists and get the charge.
        if other_legs:
            pickup_carrier = other_legs.get("pickup_carrier")
            delivery_carrier = other_legs.get("delivery_carrier")

            if pickup_carrier:
                if pickup_carrier.code == CAN_NORTH:
                    charge = p_and_d.calculate_pickup()

                    if charge:
                        other_charges.append(charge)
                        self._is_cn_pickup = True
                        instruction_fields.append("Please pick up from shipper.")

            if delivery_carrier:
                if delivery_carrier.code == CAN_NORTH:
                    charge = p_and_d.calculate_delivery()

                    if charge:
                        other_charges.append(charge)
                        self._is_cn_delivery = True
                        instruction_fields.append("Please deliver to consignee.")
                else:
                    instruction_fields.append(
                        "PLEASE HOLD FOR {} FOR FURTHERANCE TO {}".format(
                            delivery_carrier, destination_city
                        )
                    )

        instructions = " ".join(instruction_fields)[:200]

        self._skyline_request["OtherCharges"] = other_charges
        self._skyline_request["HandlingNotes"] = instructions
        self._skyline_request["SpecialInstructions"] = instructions

    def _perform_ship(self):
        """
        Perform ship call to skyline and perform resulting document calls for request.
        """
        self._skyline_response = self._post(self._skyline_request)
        self._skyline_response = self._skyline_response["data"]
        self._format_response()

        awb = self._skyline_response["AirWaybillNumber"]
        api_key = self._skyline_request["API_Key"]

        document_threads = []
        for doc_type in (DOCUMENT_TYPE_SHIPPING_LABEL, DOCUMENT_TYPE_BILL_OF_LADING):
            if doc_type == DOCUMENT_TYPE_SHIPPING_LABEL:
                url = self._cargo_labels_url
            else:
                url = self._awb_url

            document_threads.append(
                gevent.Greenlet.spawn(
                    self._download_document, doc_type, awb, api_key, url
                )
            )

        gevent.joinall(document_threads)

        self._response["documents"] = [document.get() for document in document_threads]

        if self._gobox_request.get("is_dangerous_goods", False):
            self._response["documents"].append(
                DangerousGoodsAir(self._gobox_request).generate_documents()
            )

        if str(self._sub_account.subaccount_number) in [
            "2c0148a6-69d7-4b22-88ed-231a084d2db9",
            "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
        ]:
            copied = copy.deepcopy(self._gobox_request)
            self._gobox_request["order_date"] = date.today().strftime("%Y/%m/%d")
            self._gobox_request["bol"] = awb
            self._gobox_request["bol_number"] = awb
            self._gobox_request["carrier"] = self._response["carrier_name"]
            self._gobox_request["service_name"] = self._response["service_name"]
            copied["origin"] = self._gobox_request["ultimate_origin"]
            copied["destination"] = self._gobox_request["ultimate_destination"]
            manual_docs = ManualDocuments(gobox_request=copied)

            self._response["documents"].append(
                {
                    "document": manual_docs.generate_cargo_label(),
                    "type": DOCUMENT_TYPE_COMMERCIAL_INVOICE,
                }
            )

    def ship(self) -> dict:
        """
        The function will handle building the Skyline ship requests, posting ship request, and returning
        the formatted ship response from Skyline. It also checks whether the Skyline API is active or if
        its a pickup or delivery leg. If needed it well also send any pickup or delivery notices.
        """
        self._order_number = self._gobox_request["order_number"]

        if (
            self._gobox_request.get("do_not_ship")
            or self._gobox_request["service_code"] == "PICK_DEL"
        ):
            connection.close()
            return self._do_not_ship()

        try:
            self._rate_priorities()
            self._process_packages()
        except ShipException as e:
            CeleryLogger().l_critical.delay(
                location="SkylineShip.py line: 293",
                message=str("Skyline Ship package issue: {}".format(e.message)),
            )
            connection.close()
            raise ShipException({"api.error": "Carrier account not found"})

        try:
            self._build()
        except ShipException as e:
            CeleryLogger().l_critical.delay(
                location="SkylineShip.py line: 300",
                message=str("Skyline Ship build error: {}".format(e.message)),
            )
            raise ShipException({"api.error": "Error with request: " + str(e)})

        try:
            self._perform_ship()
        except RequestError as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="SkylineShip.py line: 310",
                message="Skyline Ship error: {}".format(str(e)),
            )
            raise ShipException({"API.Error": "Error with request: " + str(e)})
        connection.close()

        p_and_d_emails = PickupDeliveryEmail(
            gobox_request=self._gobox_request,
            skyline_request=self._skyline_request,
            skyline_response=self._skyline_response,
            order_number=self._order_number,
        )

        email_threads = []
        if self._is_cn_pickup:
            email_threads.append(
                gevent.Greenlet.spawn(p_and_d_emails.send_pickup_notification)
            )

        if self._is_cn_delivery:
            email_threads.append(
                gevent.Greenlet.spawn(p_and_d_emails.send_delivery_notification)
            )

        gevent.joinall(email_threads)

        return self._response

    # Override
    def _build(self) -> None:
        """
        Build ship request for the given rate priority that belongs to the skyline account.
        """
        interline_id = None
        origin = self._gobox_request["ultimate_origin"]
        destination = self._gobox_request["ultimate_destination"]

        self._build_address(address=origin, key="Sender")
        self._build_address(address=destination, key="Recipient")
        self._build_packages()
        self._build_shipping_carriers()

        origin_airport = getkey(self._gobox_request, "origin.base")
        destination_airport = getkey(self._gobox_request, "destination.base")

        if origin_airport is None or destination_airport is None:
            CeleryLogger().l_critical.delay(
                location="SkylineShip.py line: 354",
                message="Skyline Ship: The airbase cannot be found.",
            )
            raise ShipException(
                {"api.error": "Skyline Ship: The airbase cannot be found."}
            )

        interline = GetInterlineID(
            origin=origin_airport, destination=destination_airport
        )
        is_interline = interline.check_interline_lane()

        if is_interline:
            interline_id = interline.get_interline_code()

            if not interline_id:
                raise ShipException(
                    {"api.error": "Skyline Ship: The Interline cannot be found."}
                )

        po_number = "{}/{}".format(
            self._order_number, self._gobox_request.get("reference_one", "")
        )[:40]

        base = {
            "OriginAirportCode": origin_airport,
            "DestinationAirportCode": destination_airport,
            "PurchaseOrder": po_number,
            "DescriptionOfContents": "GoBox Shipment",
            "TotalPackages": self._total_packages,
            "TotalWeight": self._total_weight,
            "API_Key": str(self._api_key),
            "CustomerId": str(self._skyline_account.customer_id),
        }

        if is_interline:
            base["InterlineGroupId"] = interline_id

        self._skyline_request.update(base)

    # Override
    def _format_response(self):
        """
        Parse Skyline responses into GoBox format
        """
        surcharges, surcharges_cost = self._process_surcharges(
            surcharge_data=self._skyline_response["Charge"]["Surcharges"]
        )
        rate_priority_code = self._gobox_request["rp"]
        rate_priority_id = self._gobox_request["rp_id"]
        origin_airport = getkey(self._gobox_request, "origin.base")
        destination_airport = getkey(self._gobox_request, "destination.base")

        charge = self._skyline_response["Charge"]

        service = self._nature_of_goods.filter(
            rate_priority_id=rate_priority_id, rate_priority_code=rate_priority_code
        ).first()
        total = Decimal(charge.get("Total")).quantize(self._sig_fig)
        taxes = Decimal(charge.get("TotalTaxes")).quantize(self._sig_fig)

        try:
            transit = Transit(
                origin=origin_airport,
                destination=destination_airport,
                service_id=int(service.rate_priority_id),
                service_code=service.rate_priority_description,
            ).transit_time()
        except Exception:
            transit = -1

        estimated_delivery_date, transit = DateUtility(
            pickup=self._gobox_request.get("pickup")
        ).get_estimated_delivery(
            transit=transit,
            country=self._gobox_request["origin"]["country"],
            province=self._gobox_request["origin"]["province"],
        )

        self._gobox_request["tracking_number"] = self._skyline_response[
            "AirWaybillNumber"
        ]
        self._gobox_request["awb"] = self._skyline_response["AirWaybillNumber"]

        self._response = {
            "total": total,
            "freight": Decimal(charge.get("Freight")).quantize(self._sig_fig),
            "taxes": taxes,
            "tax_percent": Decimal((taxes / total) * self._hundred).quantize(
                self._sig_fig
            ),
            "surcharges": surcharges,
            "surcharges_cost": surcharges_cost,
            "carrier_id": self._gobox_request["carrier_id"],
            "service_code": self._gobox_request["service_code"],
            "carrier_name": "Canadian North",
            "service_name": service.rate_priority_description,
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
            "tracking_number": self._skyline_response["AirWaybillNumber"],
            "rp": rate_priority_code,
        }

    # Override
    def _post(self, data: dict) -> Union[list, dict]:
        """
        Make Skyline ship call
        """

        try:
            response = requests.post(
                self._ship_url, json=data, timeout=DEFAULT_TIMEOUT_SECONDS
            )
        except requests.Timeout:
            connection.close()
            CeleryLogger().l_info.delay(
                location="SkylineShip.py line: 426",
                message=str("Skyline Ship posting data: {}".format(data)),
            )
            CeleryLogger().l_error.delay(
                location="SkylineShip.py line: 426",
                message=str(
                    {"api.error.skyline.ship": "Timeout exception on shipping"}
                ),
            )
            raise RequestError(None, data)
        except requests.RequestException:
            connection.close()
            raise RequestError(None, data)

        if not response.ok:
            connection.close()
            CeleryLogger().l_info.delay(
                location="SkylineShip.py line: 443",
                message=str("Skyline Ship request data: {}".format(data)),
            )
            CeleryLogger().l_info.delay(
                location="SkylineShip.py line: 443",
                message=str("Skyline Ship return data: {}".format(response.text)),
            )
            raise RequestError(None, data)

        try:
            response = response.json()
        except ValueError:
            connection.close()
            raise RequestError(None, data)
        if response["errors"]:
            CeleryLogger().l_info.delay(
                location="SkylineShip.py line: 443",
                message=str("Skyline Ship request data: {}".format(data)),
            )
            CeleryLogger().l_info.delay(
                location="SkylineShip.py line: 426",
                message=str("Skyline Ship return data: {}".format(response)),
            )
            CeleryLogger().l_error.delay(
                location="SkylineShip.py line: 426",
                message=str(
                    {"api.error.skyline.ship": "{}".format(response["errors"])}
                ),
            )
            connection.close()
            raise RequestError(response, data)

        return response
