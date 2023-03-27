"""
    Title: Leg Model
    Description: This file will contain functions for Leg Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from datetime import datetime, timedelta, time

import pytz
from dateutil import relativedelta
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.db.models.deletion import PROTECT, CASCADE
from django.db.models.expressions import Subquery
from django.db.models.fields import DateTimeField, DecimalField, CharField, BooleanField, SmallIntegerField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone
from typing import Union

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import DatabaseException, ShipException
from api.globals.carriers import RATE_SHEET_CARRIERS, SEALIFT_CARRIERS, FEDEX, FEDEX_GROUND, TWO_SHIP_CARRIERS, \
    DAY_N_ROSS, SAMEDAY, PUROLATOR, CARGO_JET
from api.globals.project import PERCENTAGE_PRECISION, MAX_PERCENTAGE_DIGITS, BASE_TEN, PRICE_PRECISION, \
    DEFAULT_CHAR_LEN, MAX_PRICE_DIGITS, LEG_IDENTIFIER_LEN, LETTER_MAPPING_LEN, MAX_CHAR_LEN, \
    DOCUMENT_TYPE_OTHER_DOCUMENT, DOCUMENT_TYPE_COMMERCIAL_INVOICE, DOCUMENT_TYPE_BILL_OF_LADING, \
    DOCUMENT_TYPE_SHIPPING_LABEL, DOCUMENT_TYPE_B13A, DOCUMENT_TYPE_DG, CURRENCY_CODE_LEN, EXCHANGE_RATE_PRECISION
from api.models import Address, Contact, Carrier, TrackingStatus, Surcharge, ShipDocument, City, ShipmentDocument
from api.models.base_table import BaseTable


class Leg(BaseTable):
    """
        Leg Model
    """
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _chl = "b72c8b2c-2e24-4763-b130-da1d233550d2"
    _LEG_TYPES = (
        ("P", "Pickup"),
        ("M", "Main"),
        ("D", "Delivery")
    )

    shipment = ForeignKey("Shipment", on_delete=CASCADE, related_name='leg_shipment')
    ship_date = DateTimeField(auto_now_add=True, editable=True)
    leg_id = CharField(
        max_length=LEG_IDENTIFIER_LEN, unique=True, help_text="The internal GO leg identifier for any type of leg"
    )
    type = CharField(max_length=LETTER_MAPPING_LEN, choices=_LEG_TYPES)

    carrier = ForeignKey(Carrier, on_delete=PROTECT, related_name='leg_carrier')
    service_code = CharField(max_length=DEFAULT_CHAR_LEN, help_text="The carrier server identifier")
    service_name = CharField(max_length=DEFAULT_CHAR_LEN, blank=True)
    origin = ForeignKey(Address, on_delete=PROTECT, related_name='leg_origin')
    destination = ForeignKey(Address, on_delete=PROTECT, related_name='leg_destination')

    markup = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="Whole Number of markup percentage: Ex: 15 for 15%"
    )

    exchange_rate_date = DateTimeField(
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc),
        help_text="Date of exchange rate.", blank=True, null=True
    )
    original_currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Currency Code rates came in.")

    exchange_rate_original_to_base = DecimalField(
        decimal_places=EXCHANGE_RATE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="Original currency exchange rate used to go to CAD.",
        default=Decimal("1.0")
    )
    exchange_rate_base_to_original = DecimalField(
        decimal_places=EXCHANGE_RATE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="CAD Exchange rate to go back to Original currency.",
        default=Decimal("1.0")
    )

    base_currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Currency Code: CAD")
    base_freight = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    base_surcharge = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    base_tax = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    base_cost = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="The sum of freight + surcharges + tax.", default=Decimal("0.0")
    )

    exchange_rate_from_base = DecimalField(
        decimal_places=EXCHANGE_RATE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="CAD Exchange rate to go back to account currency.",
        default=Decimal("1.0")
    )

    currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Account Currency")
    freight = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In Account Currency."
    )
    surcharge = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In Account Currency."
    )
    tax = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In Account Currency."
    )
    cost = DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_PRICE_DIGITS,
        help_text="The sum of freight + surcharges + tax in account currency"
    )

    tracking_identifier = CharField(max_length=MAX_CHAR_LEN, help_text="Carrier tracking number", blank=True)
    carrier_pickup_identifier = CharField(max_length=DEFAULT_CHAR_LEN, blank=True)
    carrier_api_id = CharField(max_length=DEFAULT_CHAR_LEN, blank=True, default="")
    transit_days = SmallIntegerField(
        default=0,
        help_text="The number of days the leg will be in transit. Provided by the carrier. When no amount of transit "
                  "days is provided from the carrier the value defaults to 0"
    )
    estimated_delivery_date = DateTimeField(
        help_text="The estimated delivery date provided by the carrier",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    updated_est_delivery_date = DateTimeField(
        help_text="The updated est delivery date caluclated by transit alert system.",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    delivered_date = DateTimeField(
        help_text="The actual delivery date provided by tracking updates.",
        default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )

    pickup_message = CharField(max_length=DEFAULT_CHAR_LEN, blank=True, default="")
    pickup_status = CharField(max_length=DEFAULT_CHAR_LEN, blank=True, default="")

    on_hold = BooleanField(default=True, help_text="Is the leg on hold. In other words, not shipped.")
    is_dangerous_good = BooleanField(default=False)
    is_shipped = BooleanField(default=True, help_text="Is the leg shipped, otherwise leg is canceled(False).")
    is_delivered = BooleanField(default=False, help_text="Is the leg delivered?")
    is_pickup_overdue = BooleanField(default=False, help_text="Is leg overdue for pickup?")
    is_overdue = BooleanField(default=False, help_text="Is the leg overdue for delivery?")

    class Meta:
        verbose_name = "Shipment Leg"
        verbose_name_plural = "Shipment - Legs"

    def _origin_city(self):
        return f"{self.origin.city} - {self.origin.province.code}, {self.origin.province.country.code}"

    def _destination_city(self):
        return f"{self.destination.city} - {self.destination.province.code}, {self.destination.province.country.code}"

    def one_step_save(self, params: dict, origin: Address, destination: Address, leg_id: str, shipment):

        try:
            carrier = Carrier.objects.get(code=params["carrier_id"])
        except ObjectDoesNotExist:
            raise DatabaseException({"api.backend.error": "Carrier with id " + params["carrier_id"] + " does not exist"})

        carrier_markup = shipment.subaccount.markup.get_carrier_percentage(carrier=carrier)

        # TEMP For CHL #
        if str(shipment.subaccount.subaccount_number) == self._chl and carrier.code == PUROLATOR and \
                origin.city.lower() == "les cedres" and destination.city.lower() == "ottawa":
            self.markup = Decimal("0.00")
        else:
            self.markup = carrier_markup
        # TEMP For CHL #

        self.carrier = carrier
        self.leg_id = leg_id
        self.type = leg_id[-1]
        self.shipment = shipment
        self.service_code = params["service_code"]
        self.origin = origin
        self.destination = destination
        self.cost = Decimal("0.00")
        self.freight = Decimal("0.00")
        self.surcharge = Decimal("0.00")
        self.tax = Decimal("0.00")
        self.is_dangerous_good = shipment.is_dangerous_good
        self.save()

        status = TrackingStatus.create(param_dict={
            "leg": self, "details": "Shipment has been created.", "status": "Created"
        })
        status.save()

        pickup_carriers = list(RATE_SHEET_CARRIERS) + list(SEALIFT_CARRIERS) + list(TWO_SHIP_CARRIERS) + [DAY_N_ROSS] + [SAMEDAY]

        if carrier.code in pickup_carriers and self.type != "D" or self.carrier_pickup_identifier != "":
            status = TrackingStatus.create(param_dict={
                "leg": self, "details": "Pickup has been dispatched.", "status": "Created"
            })
            status.save()

        return self

    @staticmethod
    def get_all_undelivered_legs() -> QuerySet:
        today = datetime.now().replace(tzinfo=timezone.utc)
        past_month = today - relativedelta.relativedelta(months=1)
        today = today + timedelta(days=1)
        today = today.replace(tzinfo=timezone.utc)

        exclude_carriers = RATE_SHEET_CARRIERS + SEALIFT_CARRIERS
        exclude_carriers = list(exclude_carriers)
        # exclude_carriers.remove(CARGO_JET)

        legs = Leg.objects.select_related(
            "carrier",
            "destination",
            "shipment"
        ).filter(
            ship_date__range=[past_month, today],
            is_shipped=True,
            is_delivered=False
        ).exclude(
            carrier__code__in=exclude_carriers
        ).exclude(
            pk__in=Subquery(
                TrackingStatus.objects.exclude(
                    delivered_datetime=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
                ).distinct().values("leg_id")
            )
        )

        return legs

    def create_pickup(self) -> dict:
        closing = time(hour=16).strftime('%H:%M')
        opening = time(hour=8)
        cutoff = time(hour=12)

        try:
            time_zone = City().get_timezone(
                name=self.origin.city, province=self.origin.province.code, country=self.origin.province.country.code
            )
        except (ShipException, Exception):
            time_zone = 'America/Edmonton'
        tz = pytz.timezone(time_zone)

        # Get current time with 10 min buffer
        current_time = datetime.now(tz=tz) + timedelta(minutes=10)
        current_time = current_time.time()

        # Get todays date and the next day
        current_date = datetime.today().date()
        pickup_date = current_date
        next_day = pickup_date + timedelta(days=1)

        if current_time > cutoff:
            pickup_date = next_day
        elif self.carrier.code == FEDEX and self.service_code == FEDEX_GROUND:
            pickup_date = next_day

        if pickup_date.isoweekday() == 6:
            pickup_date = pickup_date + timedelta(days=2)
        elif pickup_date.isoweekday() == 7:
            pickup_date = pickup_date + timedelta(days=1)

        if pickup_date == current_date:
            pickup_time = current_time.strftime('%H:%M')
        else:
            pickup_time = opening.strftime('%H:%M')

        return {
            "date": pickup_date.strftime("%Y-%m-%d"),
            "start_time": pickup_time,
            "end_time": closing
        }

    def next_leg_json(self, origin: Contact, destination: Contact) -> dict:
        return {
            "carrier_id": self.carrier.code,
            "service_code": self.service_code,
            "origin": self.origin.next_leg_json(origin),
            "destination": self.destination.next_leg_json(destination),
            "pickup": self.create_pickup()
        }

    def update_leg(self, update_params: dict, exchange_rate: Decimal, on_hold: bool = False) -> None:
        """
            Update Leg with shipped information.
            :param update_params:
            :param exchange_rate:
            :param on_hold:
            :return:
        """

        Surcharge.objects.bulk_create([
            Surcharge(
                name=surcharge["name"],
                cost=surcharge["cost"],
                percentage=surcharge["percentage"],
                leg=self)
            for surcharge in update_params["surcharges"]
        ])

        update_params["surcharges"] = update_params["surcharges_cost"]

        freight = update_params.get('un_freight', Decimal("0.00"))
        surcharges = update_params["surcharges"]
        tax = update_params.get('un_taxes', Decimal("0.00"))
        total = update_params.get('un_total', Decimal("0.00"))

        del update_params["surcharges_cost"]
        del update_params['un_total']
        del update_params['un_freight']
        del update_params['un_taxes']

        self.exchange_rate_date = datetime.now(tz=pytz.UTC)

        self.base_freight = freight.quantize(self._price_sig_fig)
        self.base_surcharge = surcharges.quantize(self._price_sig_fig)
        self.base_tax = tax.quantize(self._price_sig_fig)
        self.base_cost = total.quantize(self._price_sig_fig)

        self.exchange_rate_from_base = exchange_rate
        self.currency = self.shipment.subaccount.currency_code

        self.freight = (freight * exchange_rate).quantize(self._price_sig_fig)
        self.surcharge = (surcharges * exchange_rate).quantize(self._price_sig_fig)
        self.tax = (tax * exchange_rate).quantize(self._price_sig_fig)
        self.cost = (total * exchange_rate).quantize(self._price_sig_fig)

        self.service_name = update_params.get('service_name', '')
        self.transit_days = update_params.get('transit_days', -1)
        self.on_hold = on_hold

        pickup_id = update_params.get("pickup_id", "")
        tracking_identifier = update_params.get('tracking_number', '')

        if not tracking_identifier:
            tracking_identifier = ""

        if not pickup_id:
            pickup_id = ""

        self.tracking_identifier = tracking_identifier
        self.carrier_pickup_identifier = pickup_id

        if update_params.get("delivery_date"):
            try:
                delivery_date = datetime.strptime(update_params["delivery_date"], "%Y-%m-%dT%H:%M:%S")
                self.estimated_delivery_date = delivery_date
                self.updated_est_delivery_date = delivery_date
            except Exception as e:
                CeleryLogger().l_error.delay(
                    location="shipment_leg.py line: 339",
                    message=f"Delivery date: {update_params['delivery_date']}\n {str(e)}"
                )
                pass

        if 'carrier_api_id' in update_params:
            self.carrier_api_id = update_params["carrier_api_id"]
            del update_params['carrier_api_id']

        if 'pickup_status' in update_params:
            self.pickup_status = update_params["pickup_status"]
            del update_params['pickup_status']

        if 'pickup_message' in update_params:
            self.pickup_message = update_params["pickup_message"][:DEFAULT_CHAR_LEN]
            del update_params['pickup_message']

        if "exchange_rate" in update_params:
            self.original_currency = update_params["exchange_rate"]["from_currency"]
            self.exchange_rate_original_to_base = update_params["exchange_rate"]["from_source"]
            self.exchange_rate_base_to_original = update_params["exchange_rate"]["to_source"]
            del update_params['exchange_rate']

        self.save()

        for document in update_params.get("documents", []):

            if document['type'] in [DOCUMENT_TYPE_COMMERCIAL_INVOICE, DOCUMENT_TYPE_B13A, DOCUMENT_TYPE_DG]:
                ShipmentDocument.add_document(self.shipment, document['document'], document['type'])
            else:
                ShipDocument.add_document(self, document['document'], document['type'])

    @property
    def packing_label(self) -> Union[str, None]:
        document = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_SHIPPING_LABEL).first()
        if document is None:
            return None
        return document.document

    @property
    def shipping_label(self) -> Union[str, None]:
        document = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_BILL_OF_LADING).first()
        if document is None:
            return None
        return document.document

    @property
    def commercial_invoice(self) -> Union[str, None]:
        document = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_COMMERCIAL_INVOICE).first()
        if document is None:
            return None
        return document.document

    @property
    def dangerous_label(self) -> Union[str, None]:
        document = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_OTHER_DOCUMENT).first()
        if document is None:
            return None
        return document.document

    def to_json(self):
        is_cargo_labels = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_SHIPPING_LABEL).exists()
        is_bol_awb_labels = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_BILL_OF_LADING).exists()
        is_commercial_labels = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_COMMERCIAL_INVOICE).exists()
        is_other_labels = self.shipdocument_leg.filter(type=DOCUMENT_TYPE_OTHER_DOCUMENT).exists()

        multiplier = (self.markup / 100) + 1

        return {
            "leg_id": self.leg_id,
            "carrier": self.carrier.name,
            "service": self.service_name,
            "reference": self.tracking_identifier,
            "pickup_number": self.carrier_pickup_identifier,
            "origin": self.origin.get_ship_dict,
            "destination": self.destination.get_ship_dict,
            "freight": self.freight,
            "surcharges_total": self.surcharge,
            "tax": self.tax,
            "total": self.cost,
            "markup": self.markup,
            "markup_surcharges": Decimal(self.surcharge * multiplier).quantize(self._price_sig_fig),
            "markup_freight": Decimal(self.freight * multiplier).quantize(self._price_sig_fig),
            "markup_tax": Decimal(self.tax * multiplier).quantize(self._price_sig_fig),
            "markup_total": Decimal(self.cost * multiplier).quantize(self._price_sig_fig),
            "surcharges": [
                surcharge.to_json()
                for surcharge in self.surcharge_leg.all()
            ],
            "is_cargo_label": is_cargo_labels,
            "is_bol_awb_label": is_bol_awb_labels,
            "is_commercial_label": is_commercial_labels,
            "is_other_label": is_other_labels
        }

    @property
    def to_api_json(self):

        multiplier = (self.markup / 100) + 1

        ret = {
            "leg_id": self.leg_id,
            "carrier": self.carrier.name,
            "service": self.service_name,
            "reference": self.tracking_identifier,
            "pickup_number": self.carrier_pickup_identifier,
            "origin": {
                "address": self.origin.address,
                "address_two": self.origin.address_two,
                "city": self.origin.city,
                "province": self.origin.province.code,
                "country": self.origin.province.country.code,
                "postal_code": self.origin.postal_code
            },
            "destination": {
                "address": self.destination.address,
                "address_two": self.destination.address_two,
                "city": self.destination.city,
                "province": self.destination.province.code,
                "country": self.destination.province.country.code,
                "postal_code": self.destination.postal_code
            },
            "surcharges": Decimal(self.surcharge * multiplier).quantize(self._price_sig_fig),
            "freight": Decimal(self.freight * multiplier).quantize(self._price_sig_fig),
            "tax": Decimal(self.tax * multiplier).quantize(self._price_sig_fig),
            "total": Decimal(self.cost * multiplier).quantize(self._price_sig_fig),
        }

        if self.shipment.user.username == "GoBox":
            ret["markup"] = self.markup

        return ret

    # Override
    def __repr__(self) -> str:
        if self.on_hold:
            return f"< ShipmentLeg ({self.leg_id}, {self.carrier}: {self.origin.city} to " \
                f"{self.destination.city}, OnHold) >"
        return f"< ShipmentLeg ({self.leg_id}, {self.carrier}: {self.origin.city} to " \
            f"{self.destination.city}, Shipped) >"

    # Override
    def __str__(self) -> str:
        if self.on_hold:
            return f"{self.leg_id}, {self.carrier}: {self.origin.city} to {self.destination.city}, OnHold"
        return f"{self.leg_id}, {self.carrier}: {self.origin.city} to {self.destination.city}, Shipped"
