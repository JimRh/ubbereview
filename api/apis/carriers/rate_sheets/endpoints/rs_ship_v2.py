"""
    Title: RateSheet Ship
    Description: This file will contain functions related to Shipping.
    Created: February 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
# TODO: Remove Email from this file.

import datetime
from decimal import Decimal, ROUND_HALF_UP

import gevent
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.utils import timezone

from api.apis.carriers.rate_sheets.endpoints.rs_api_v2 import RateSheetAPI
from api.apis.carriers.rate_sheets.endpoints.rs_email_v2 import RateSheetEmail
from api.apis.services.taxes.taxes import Taxes
from api.background_tasks.logger import CeleryLogger
from api.documents.commercial_invoice import CommercialInvoice
from api.documents.manual_documents import ManualDocuments
from api.exceptions.project import ShipException, RequestError
from api.globals.carriers import (
    SEALIFT_CARRIERS,
    AIR_CARRIERS,
    KEEWATIN_AIR,
    PANORAMA_AIR,
    FATHOM,
    BUFFALO_AIRWAYS,
)
from api.globals.project import (
    DOCUMENT_TYPE_SHIPPING_LABEL,
    DOCUMENT_TYPE_BILL_OF_LADING,
    DOCUMENT_TYPE_COMMERCIAL_INVOICE,
    DOCUMENT_TYPE_NEAS,
)
from api.models import Dispatch, RateSheet, API
from api.utilities.date_utility import DateUtility


class RateSheetShip(RateSheetAPI):
    _cubic_in_constant = 1728
    _freight_classes = {
        (50, 10000): "050",
        (35, 50): "055",
        (22.5, 35): "065",
        (13.5, 22.5): "070",
        (12, 13.5): "085",
        (10.5, 12): "092",
        (9, 10.5): "100",
        (8, 9): "110",
        (7, 8): "125",
        (6, 7): "150",
        (5, 6): "175",
        (4, 5): "200",
        (3, 4): "250",
        (2, 3): "300",
        (1, 2): "400",
        (0, 1): "500",
    }

    def __init__(self, ubbe_request: dict) -> None:
        super(RateSheetShip, self).__init__(ubbe_request=ubbe_request)

        self._carrier_id = self._ubbe_request["carrier_id"]
        self._sub_account = self._ubbe_request["objects"]["sub_account"]
        self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
            self._carrier_id
        ]["account"]
        self._carrier = self._ubbe_request["objects"]["carrier_accounts"][
            self._carrier_id
        ]["carrier"]

        if "dg_service" in self._ubbe_request:
            self._dg_service = self._ubbe_request.pop("dg_service")
        else:
            self._dg_service = None

    def _add_freight_class(self):
        """
        Create lxml package data for request
        :return: package lxml object
        """

        for package in self._ubbe_request["packages"]:
            quantity = package["quantity"]
            length = package["imperial_length"]
            width = package["imperial_width"]
            height = package["imperial_height"]
            weight = package["imperial_weight"]
            volume = ((length * width * height) * quantity) / self._cubic_in_constant
            freight_class = self._get_freight_class(weight=weight, volume=volume)
            package["freight_class"] = freight_class

    def _get_bol_number(self, dispatch: Dispatch) -> str:
        """
        Get BOL Number for carrier if one exists.
        :param dispatch:
        :return: BOL Number or Empty String
        """

        bill_of_lading = dispatch.bol_dispatch.filter(is_available=True).first()

        if bill_of_lading:
            bill_of_lading.is_available = False
            bill_of_lading.save()
            return bill_of_lading.bill_of_lading

        if "awb" in self._ubbe_request and self._carrier_id in AIR_CARRIERS:
            return self._ubbe_request["awb"]

        return ""

    def _get_dispatch(self) -> Dispatch:
        """
        Get dispatch for carrier city terminal, if none exist get the default one.
        :return:
        """

        try:
            dispatch = Dispatch.objects.get(
                carrier=self._carrier, location=self._origin["city"]
            )
        except ObjectDoesNotExist:
            dispatch = Dispatch.objects.get(carrier=self._carrier, is_default=True)

        return dispatch

    def _get_documents(self) -> list:
        """
        Generate Documents: BOL, Cargo Labels. If needed: CI and Sealift Forms.
        :return: list of pdfs
        """

        manual_docs = ManualDocuments(gobox_request=self._ubbe_request)

        if self._carrier_id in AIR_CARRIERS:
            if self._carrier_id in [KEEWATIN_AIR, PANORAMA_AIR, BUFFALO_AIRWAYS]:
                bol_thread = gevent.Greenlet.spawn(manual_docs.generate_bol)
            else:
                bol_thread = gevent.Greenlet.spawn(
                    manual_docs.generate_airwaybill, self._carrier_id
                )
        else:
            bol_thread = gevent.Greenlet.spawn(manual_docs.generate_bol)

        piece_label_thread = gevent.Greenlet.spawn(manual_docs.generate_cargo_label)
        threads = [bol_thread, piece_label_thread]

        if self._ubbe_request["is_international"]:
            commercial = CommercialInvoice(
                shipdata=self._ubbe_request,
                order_number=self._ubbe_request["order_number"],
            )
            commercial_invoice_thread = gevent.Greenlet.spawn(commercial.get_base_64)
            threads.append(commercial_invoice_thread)

        gevent.joinall(threads)

        piece_label = piece_label_thread.value
        bol = bol_thread.value

        documents = [
            {"document": piece_label, "type": DOCUMENT_TYPE_SHIPPING_LABEL},
            {"document": bol, "type": DOCUMENT_TYPE_BILL_OF_LADING},
        ]

        if self._ubbe_request.get("is_dangerous_goods", False):
            documents.append(self._dg_service.generate_documents())

        if self._ubbe_request["is_international"]:
            commercial_invoice = commercial_invoice_thread.value
            documents.append(
                {
                    "document": commercial_invoice,
                    "type": DOCUMENT_TYPE_COMMERCIAL_INVOICE,
                }
            )

        if self._carrier_id in SEALIFT_CARRIERS and self._carrier_id != FATHOM:
            sealift_form = manual_docs.generate_sealift_form()
            documents.append({"document": sealift_form, "type": DOCUMENT_TYPE_NEAS})

        return documents

    def _get_freight_class(self, volume: Decimal, weight: Decimal):
        actual_density = Decimal(weight) / Decimal(volume)
        for density, freight_class in self._freight_classes.items():
            if density[0] <= actual_density < density[1]:
                return freight_class

    def _set_email_information(
        self, rate_sheet: RateSheet, dispatch: Dispatch, is_sealift: bool
    ):
        """
        Set necessary email information for request email.
        """
        self._ubbe_request["carrier"] = self._carrier.name
        self._ubbe_request["carrier_name"] = self._carrier.name
        self._ubbe_request["is_carrier_metric"] = self._carrier.is_kilogram
        self._ubbe_request["service"] = rate_sheet.service_name
        self._ubbe_request["service_name"] = rate_sheet.service_name
        self._ubbe_request[
            "carrier_account"
        ] = self._carrier_account.account_number.decrypt()
        self._ubbe_request["carrier_email"] = dispatch.email
        self._ubbe_request["request_date"] = self._date.strftime("%Y/%m/%d")
        self._ubbe_request["is_sealift"] = False
        self._ubbe_request["is_bbe"] = (
            str(self._sub_account.subaccount_number) in self._bbe_account
        )

        if not self._ubbe_request.get("pickup"):
            self._ubbe_request["pickup"] = {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "start_time": "08:00",
                "end_time": "16:00",
            }

        if is_sealift:
            sailing = self._ubbe_request["objects"]["sailing"]
            self._ubbe_request["sailing_port"] = sailing.port.name
            self._ubbe_request["service_name"] = sailing.get_name_display()
            self._ubbe_request["sailing_date"] = sailing.sailing_date.strftime(
                "%Y/%m/%d"
            )
            self._ubbe_request["is_sealift"] = True

    def _process_city_alias(self):
        """
        Get City Alias for both Origin and Destination.
        :return: str tuple of cities
        """

        from_city = self._get_city_alias(
            city=self._origin["city"],
            province=self._origin["province"],
            country=self._origin["country"],
        )

        to_city = self._get_city_alias(
            city=self._destination["city"],
            province=self._destination["province"],
            country=self._destination["country"],
        )

        return from_city, to_city

    def _process_surcharges(
        self,
        sheet: RateSheet,
        freight_cost: Decimal,
        final_weight: Decimal,
        is_metric: bool,
    ) -> tuple:
        """
        Process Shipment Surcharges
        :param sheet: RateSheet Object
        :param freight_cost: Freight cost
        :param is_metric: is the shipment metric or imperial.
        :return: tuple with surcharges, surcharges_cost, option_names
        """
        surcharges_cost = Decimal("0.00")

        # Get Carrier and Mandatory Options
        surcharges = self._get_carrier_options(
            sheet=sheet, freight_cost=freight_cost, is_metric=is_metric
        )
        surcharges.extend(
            self._get_mandatory_options(
                sheet=sheet, freight_cost=freight_cost, is_metric=is_metric
            )
        )

        for option in surcharges:
            surcharges_cost += option["cost"]

        # Get Fuel Surcharge
        fuel_surcharge = self._get_fuel_surcharge_cost(
            carrier_id=sheet.carrier.code,
            final_weight=final_weight,
            freight_cost=freight_cost,
        )

        if fuel_surcharge["cost"] != self._zero:
            surcharges_cost += fuel_surcharge["cost"]
            surcharges.append(fuel_surcharge)

        option_names = [option["name"] for option in surcharges]

        return surcharges, surcharges_cost, option_names

    def _ship_ground(self, dispatch: Dispatch):
        today = datetime.datetime.now().replace(tzinfo=timezone.utc)
        from_city, to_city = self._process_city_alias()

        try:
            sheet = RateSheet.objects.get(
                sub_account=self._sub_account,
                origin_city=from_city,
                destination_city=to_city,
                origin_province__country__code=self._origin["country"],
                destination_province__country__code=self._destination["country"],
                origin_province__code=self._origin["province"],
                destination_province__code=self._destination["province"],
                carrier__code=self._carrier_id,
                service_code=self._ubbe_request["service_code"],
            )
        except ObjectDoesNotExist:
            try:
                sheet = RateSheet.objects.get(
                    sub_account__is_default=True,
                    origin_city=from_city,
                    destination_city=to_city,
                    origin_province__country__code=self._origin["country"],
                    destination_province__country__code=self._destination["country"],
                    origin_province__code=self._origin["province"],
                    destination_province__code=self._destination["province"],
                    carrier__code=self._carrier_id,
                    service_code=self._ubbe_request["service_code"],
                )
            except ObjectDoesNotExist:
                connection.close()
                raise ShipException(
                    {"api.error.rate_sheets.ship": "No lanes for selected carrier"}
                )

        if sheet.expiry_date <= today:
            # Skip rate sheet as it as expired
            raise ShipException({"api.error.rate_sheets.ship": "The lane is expired."})

        dimensional_weight = self._total_volume_imperial * sheet.carrier.linear_weight
        final_weight = max(dimensional_weight, self._total_mass_imperial)
        final_weight = Decimal(final_weight).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )

        try:
            freight = self._get_freight_cost(sheet=sheet, weight=final_weight)
        except ShipException as e:
            CeleryLogger().l_info.delay(
                location="RateSheetShip.py line: 101", message=e.message
            )
            connection.close()
            raise ShipException(
                {"api.error.rate_sheets.ship": "Rate could not be determined: {}"}
            )

        surcharges, surcharges_cost, option_names = self._process_surcharges(
            sheet=sheet,
            freight_cost=freight,
            final_weight=final_weight,
            is_metric=False,
        )
        self._set_email_information(
            rate_sheet=sheet, dispatch=dispatch, is_sealift=False
        )

        return sheet, surcharges, surcharges_cost, option_names, freight

    def _ship_sealift(self, dispatch: Dispatch):
        rate_sheets = self._get_rate_sheets_sealift(carrier_id=self._carrier_id)

        freight, crate_cost, sheet = self._process_package_costs(
            sheets=rate_sheets, packages=self._packages
        )

        surcharges, surcharges_cost, option_names = self._process_surcharges(
            sheet=sheet,
            freight_cost=freight,
            final_weight=self._total_mass_metric,
            is_metric=False,
        )
        surcharges_cost += crate_cost

        self._set_email_information(
            rate_sheet=sheet, dispatch=dispatch, is_sealift=True
        )

        return sheet, surcharges, surcharges_cost, option_names, freight

    def get_ground_cost(self):
        """

        :return:
        """
        dispatch = self._get_dispatch()

        sheet, surcharges, surcharges_cost, option_names, freight = self._ship_ground(
            dispatch=dispatch
        )

        return {
            "surcharges": surcharges,
            "surcharges_cost": surcharges_cost,
            "freight": freight,
        }

    def ship(self, order_number: str = "") -> dict:
        """
        Ship a RateSheet Carrier.
        :return: Shipment Details
        """

        if self._ubbe_request["is_international"]:
            self._add_freight_class()

        dispatch = self._get_dispatch()

        if self._carrier_id in SEALIFT_CARRIERS:
            if not API.objects.get(name="Sealift").active:
                connection.close()
                raise ShipException(
                    {"api.error.sealift.ship": "Sealift API not active"}
                )

            (
                sheet,
                surcharges,
                surcharges_cost,
                option_names,
                freight,
            ) = self._ship_sealift(dispatch=dispatch)

            service_code = self._ubbe_request["service_code"]
            service_name = self._ubbe_request["service_name"]
        else:
            (
                sheet,
                surcharges,
                surcharges_cost,
                option_names,
                freight,
            ) = self._ship_ground(dispatch=dispatch)

            service_code = sheet.service_code
            availability = sheet.availability
            service_name = sheet.service_name

            if availability:
                service_name = "{} (ships {})".format(service_name, availability)

        bol_number = self._get_bol_number(dispatch=dispatch)
        self._ubbe_request["bol"] = bol_number
        self._ubbe_request["bol_number"] = bol_number
        self._ubbe_request["tracking_number"] = bol_number
        self._ubbe_request["option_names"] = option_names

        try:
            documents = self._get_documents()
        except ShipException:
            connection.close()
            raise

        try:
            taxes = Taxes(self._destination).get_tax_rate(freight + surcharges_cost)
        except RequestError:
            connection.close()
            raise ShipException({"api.error.rate_sheets.ship": "Error fetching tax"})

        if sheet.transit_days > 0:
            transit = sheet.transit_days + 1
        else:
            transit = sheet.transit_days

        estimated_delivery_date, transit = DateUtility(
            pickup=self._ubbe_request["pickup"]
        ).get_estimated_delivery(
            transit=transit,
            country=self._origin["country"],
            province=self._origin["province"],
        )

        ship_return = {
            "carrier_id": sheet.carrier.code,
            "carrier_name": sheet.carrier.name,
            "documents": documents,
            "freight": freight,
            "service_code": service_code,
            "service_name": service_name,
            "surcharges": surcharges,
            "surcharges_cost": surcharges_cost,
            "taxes": taxes,
            "tax_percent": (
                (taxes / (freight + surcharges_cost)) * self._hundred
            ).quantize(self._sig_fig),
            "total": freight + surcharges_cost + taxes,
            "tracking_number": bol_number,
            "transit_days": transit,
            "delivery_date": estimated_delivery_date,
        }

        if sheet.currency != "CAD":
            self._apply_exchange_rate(sheet=sheet, data=ship_return, is_ship=True)

        if self._ubbe_request["is_pickup"]:
            try:
                RateSheetEmail(self._ubbe_request).manual_email()
            except Exception as e:
                connection.close()
                CeleryLogger().l_critical.delay(
                    location="RateSheetShip.py line: 319", message=str(e)
                )

        connection.close()
        return ship_return
