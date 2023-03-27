"""
    Title: Cargojet Ship Api
    Description: This file will contain functions related to Cargojet Ship Apis.
    Created: Sept 27, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.db import connection

from api.apis.carriers.cargojet.endpoints.cj_api import CargojetApi
from api.apis.carriers.rate_sheets.endpoints.rs_ship_v2 import RateSheetShip
from api.apis.services.taxes.taxes import Taxes
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RequestError, ShipException
from api.globals.carriers import CARGO_JET
from api.utilities.date_utility import DateUtility


class CargojetShip(CargojetApi):
    """
    Cargojet Ship Class

    T -> TWODAY
    S -> STANDBY
    N -> Normal (Current BBE service)

    """

    def __init__(self, ubbe_request: dict) -> None:
        super().__init__(ubbe_request=ubbe_request)
        self._response = {}

    @staticmethod
    def _get_service_type(origin: str, destination: str) -> str:
        """
        Get Shipper or Consignee code for airport location.
        :return:
        """
        lane = f"{origin}-{destination}"

        if lane in ["YEG-YOW", "YEG-YMX", "YEG-YHM", "YEG-YYZ", "YEG-YVR", "YOW-YEG"]:
            service_type = "LLI"
        else:
            service_type = "LL"

        return service_type

    @staticmethod
    def _build_address(address: dict, address_code: str) -> dict:
        """
        Build cargojet address structure
        :param address: ubbe request address
        :return: dict of address details
        """
        return {
            f"{address_code}NAME": f'{address["company_name"]}/{address["name"]}',
            f"{address_code}ADR": address["address"],
            f"{address_code}CTY": address["city"],
            f"{address_code}CNT": address["country"],
        }

    def _get_booking_date(self, booking_date):
        """
        Get booking date for the shipment.
        :param self:
        :param booking_date:
        :return:
        """

        now_date = datetime.datetime.now()

        if booking_date:
            booking_date = datetime.datetime.strptime(booking_date, "%Y-%m-%d")
            booking_date = booking_date + datetime.timedelta(seconds=10)

            if now_date > booking_date:
                booking_date = booking_date + datetime.timedelta(days=1)
        else:
            booking_date = now_date + datetime.timedelta(days=1)

        return booking_date.strftime("%Y-%m-%d %H:%M:%S")

    def _build(self) -> dict:
        """
        Build cargojet booking request format.
        :return: Booking Json
        """
        origin_code = self._ubbe_request["origin"]["base"]
        destination_code = self._ubbe_request["destination"]["base"]
        service_type = self._get_service_type(
            origin=origin_code, destination=destination_code
        )

        if self._ubbe_request.get("is_dangerous_goods", False):
            service_type = "LL"

        origin = self._ubbe_request["origin"]
        destination = self._ubbe_request["destination"]
        packages = self._build_packages(service_type=service_type)

        ret = {
            "TENDER_ID": self._ubbe_request["order_number"],
            "BKGDATE": self._get_booking_date(self._ubbe_request.get("booking_date")),
            "PRTY": self._ubbe_request["service_code"],
            "ORIG": origin_code,
            "DEST": destination_code,
            "SHIPORIG": origin_code,
            "SHIPDEST": destination_code,
            "CUSCOD": self._customer_code,
            "SHPCOD": "",
            "SHPNAME": f'{origin["company_name"]}/{origin["name"]}',
            "SHPADR": origin["address"],
            "SHPCTY": origin["city"],
            "SHPCNT": origin["country"],
            "CONCOD": "",
            "CONNAME": f'{destination["company_name"]}/{destination["name"]}',
            "CONADR": destination["address"],
            "CONCTY": destination["city"],
            "CONCNT": destination["country"],
            "INBOND": "N",
            "REFNUM": f'{self._ubbe_request.get("reference_one", "")}/{self._ubbe_request.get("reference_two", "")}'[
                :15
            ],
            "COMINS": "ubbe (BBE Expediting Ltd)",
            "SPEINS": self._ubbe_request.get("special_instructions", "")[:500],
            "BKGUNT": "F3",
            "SHIPPING": packages,
        }

        return ret

    def _build_packages(self, service_type: str) -> list:
        """
        Build cargojet package list.
        :return: cargojet package format
        """
        package_list = []

        for package in self._ubbe_request["packages"]:
            package_type = package["package_type"]

            if package_type in ["PHCONR", "PHEXR", "PHFRO", "PHREF"]:
                code = self._commodity_drug
            elif package_type in ["ENVELOPE"]:
                code = self._commodity_mail
            else:
                code = self._commodity_gen

            if self._ubbe_request.get("is_food", False):
                code = self._commodity_food

            if package.get("is_dangerous_good", False):
                code = self._commodity_dg

            package_list.append(
                {
                    "COMM": code,
                    "SRVICE": service_type,
                    "PIECES": package["quantity"],
                    "SHPLEN": package["imperial_length"],
                    "SHPWID": package["imperial_width"],
                    "SHPHGT": package["imperial_height"],
                    "SHPWGT": package["imperial_weight"],
                }
            )

        return package_list

    def _get_service_name(self) -> str:
        """
        Get Service Name for cargojet.
        :return:
        """

        if self._ubbe_request["service_code"] == "T":
            service_name = self._two_day_service
        elif self._ubbe_request["service_code"] == "S":
            service_name = self._standby_service
        else:
            service_name = self._normal_service

        return service_name

    def _get_shipper_consignee_code(self, airport: str) -> str:
        """
        Get Shipper or Consignee code for airport location.
        :return:
        """

        if self._yyc == airport:
            code = "BBEYYC"
        elif self._yvr == airport:
            code = "BBEYVR"
        elif self._ywg == airport:
            code = "BBEYWG"
        elif self._yqm == airport:
            code = "BBEYQM"
        elif self._yyt == airport:
            code = "BBEYYT"
        elif self._yhz == airport:
            code = "BBEYHZ"
        elif self._ymx == airport:
            code = "BBEYMX"
        elif self._yow == airport:
            code = "BBEYOW"
        elif self._yhm == airport:
            code = "BBEYHM"
        elif self._yyz == airport:
            code = "BBEYYZ"
        elif self._yqr == airport:
            code = "BBEYQR"
        elif self._yxe == airport:
            code = "BBEYXE"
        else:
            # AD HOC
            code = "BBEYEG"

        return code

    def _format_response(self, response: dict):
        """
        Process cargojet ship response and format into ubbe shipment ship response.
        :return: dict of ship
        """
        rs_ship = RateSheetShip(ubbe_request=copy.deepcopy(self._ubbe_request))

        try:
            costs = rs_ship.get_ground_cost()
            freight = costs["freight"]
            surcharges_cost = costs["surcharges_cost"]
            surcharges = costs["surcharges"]
        except Exception as e:
            CeleryLogger.l_critical(location="dfevvqe", message=f"{e}")
            raise ShipException(
                {"api.error.cargojet.ship": f"Error getting shipping cost. {e}"}
            ) from e

        sub_total = freight + surcharges_cost

        try:
            taxes = Taxes(self._ubbe_request["destination"]).get_tax_rate(sub_total)
        except RequestError as e:
            connection.close()
            raise ShipException(
                {"api.error.cargojet.ship": "Error fetching tax"}
            ) from e

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request.get("pickup", {})
        ).get_estimated_delivery(
            transit=self._transit_time,
            country=self._ubbe_request["origin"]["country"],
            province=self._ubbe_request["origin"]["province"],
        )

        self._response = {
            "carrier_id": CARGO_JET,
            "carrier_name": self._carrier_name,
            "service_code": self._ubbe_request["service_code"],
            "service_name": self._get_service_name(),
            "freight": freight,
            "surcharges": surcharges,
            "surcharges_cost": surcharges_cost,
            "tax_percent": ((taxes / sub_total) * self._hundred).quantize(
                self._sig_fig
            ),
            "taxes": taxes,
            "total": Decimal(sub_total + taxes).quantize(self._sig_fig),
            "tracking_number": response["AWB"],
            "pickup_id": "",
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
            "carrier_api_id": response["UBR"],
        }

    def ship(self) -> dict:
        """
        Ship cargojet shipment.
        :return:
        """

        try:
            request = self._build()
        except KeyError as e:
            connection.close()
            raise ShipException(f"CJ Ship (L218): {str(e)}") from e

        try:
            response = self._post(url=f"{self._url}/create_booking", data=request)
            # response = {'Results': 'Booking Created Successfuly.', 'TENDER_ID': 'ub6366323419M', 'UBR': '4211416', 'AWB': '489-35065704'}
        except RequestError as e:
            connection.close()
            raise ShipException(f"CJ Ship (L224): {str(e)}") from e

        if response.get("Results") == "Booking not Created.":
            raise ShipException(
                f'CJ Ship (L230): {response.get("TENDER_ID", "")}\n{response.get("Errors", "")}\n{request}'
            )

        try:
            self._format_response(response=response)
        except ShipException as e:
            connection.close()
            raise ShipException(
                f"CJ Ship (L234): {str(e.message)}\n{response}\n{request}"
            ) from e
        except Exception as e:
            connection.close()
            raise ShipException(
                f"CJ Ship (L234): {str(e)}\n{response}\n{request}"
            ) from e

        connection.close()
        return self._response
