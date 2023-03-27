"""
    Title: Shipment Model
    Description: This file will contain functions for Shipment Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import random
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.aggregates import Sum
from django.db.models.deletion import PROTECT
from django.db.models.fields import DateTimeField, DecimalField, CharField, TextField, BooleanField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone

from api.apis.promo_code.promo_code import PromoCodeUtility
from api.exceptions.project import ViewException
from api.globals.project import PERCENTAGE_PRECISION, MAX_PERCENTAGE_DIGITS, BASE_TEN, PRICE_PRECISION, \
    SHIPMENT_IDENTIFIER_LEN, DEFAULT_CHAR_LEN, MAX_PRICE_DIGITS, GO_PREFIX, getkey, ID_LENGTH, MAX_INSURANCE_DIGITS, \
    NO_INSURANCE, CURRENCY_CODE_LEN
from api.models import Address, Contact, SubAccount, Leg, Commodity, Airport
from api.models.base_table import BaseTable
from api.models.shipment_package import Package
from api.utilities.date_utility import DateUtility


class Shipment(BaseTable):
    """
        Shipment Model
    """
    _price_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _default_date = datetime(year=1, month=1, day=1, tzinfo=timezone.utc)

    user = ForeignKey(User, on_delete=PROTECT)
    subaccount = ForeignKey(SubAccount, on_delete=PROTECT, null=True)
    bc_customer_code = CharField(
        max_length=DEFAULT_CHAR_LEN, default="", help_text="BC Customer Code", null=True, blank=True
    )
    bc_customer_name = CharField(
        max_length=DEFAULT_CHAR_LEN, default="", help_text="BC Customer Name", null=True, blank=True
    )
    creation_date = DateTimeField(auto_now_add=True, editable=True)
    shipment_id = CharField(
        max_length=SHIPMENT_IDENTIFIER_LEN,
        unique=True,
        help_text="The internal GO shipping identifier for the shipment"
    )
    account_id = CharField(
        max_length=SHIPMENT_IDENTIFIER_LEN,
        unique=True,
        help_text="External Tracking identifier for the shipment.",
        null=True,
        blank=True
    )
    quote_id = CharField(max_length=DEFAULT_CHAR_LEN, help_text="Quote ID.", null=True, blank=True)
    ff_number = CharField(
        max_length=DEFAULT_CHAR_LEN, blank=True, help_text="Freight Forwarding number from Business Central."
    )
    origin = ForeignKey(Address, on_delete=PROTECT, related_name='shipment_origin')
    sender = ForeignKey(Contact, on_delete=PROTECT, related_name='shipment_sender')
    destination = ForeignKey(Address, on_delete=PROTECT, related_name='shipment_destination')
    receiver = ForeignKey(Contact, on_delete=PROTECT, related_name='shipment_reciver')
    billing = ForeignKey(Address, on_delete=PROTECT, related_name='shipment_billing', null=True, blank=True)
    payer = ForeignKey(Contact, on_delete=PROTECT, related_name='shipment_payer', null=True, blank=True)
    broker_address = ForeignKey(Address, on_delete=PROTECT, related_name='shipment_broker_address', null=True, blank=True)
    broker = ForeignKey(Contact, on_delete=PROTECT, related_name='shipment_broker', null=True, blank=True)

    # TODO - Deprecate markup field, these sums will be sums of the legs.
    markup = DecimalField(
        decimal_places=PERCENTAGE_PRECISION,
        max_digits=MAX_PERCENTAGE_DIGITS,
        help_text="Whole Number of markup percentage: Ex: 15 for 15%"
    )

    base_currency = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Currency Code: CAD")
    base_freight = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    base_surcharge = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    base_tax = DecimalField(decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="In CAD.", default=Decimal("0.0"))
    base_cost = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="The sum of freight + surcharges + tax.", default=Decimal("0.0")
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
        help_text="The sum of freight + surcharges + tax in account currency."
    )

    insurance_amount = DecimalField(
        decimal_places=PRICE_PRECISION,
        max_digits=MAX_INSURANCE_DIGITS,
        default=NO_INSURANCE,
        help_text="Any value greater than 0 (zero) indicates the shipment has insurance and how much, "
                  "otherwise the shipment has no insurance. (Value of Goods)"
    )
    insurance_cost = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, default=0, help_text="What we charge the customer"
    )

    promo_code_discount = DecimalField(
        decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, default=0, help_text="Promo Code discount amount"
    )

    promo_code = CharField(
        blank=True,
        max_length=DEFAULT_CHAR_LEN,
        help_text="Promo Code used in the shipment, blank means no promo code used."
    )

    purchase_order = CharField(max_length=DEFAULT_CHAR_LEN, blank=True, help_text="AKA: PO Num")
    project = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="Project shipment belongs to.")
    reference_one = TextField(blank=True)
    reference_two = TextField(blank=True)
    special_instructions = TextField(blank=True, help_text="Special Instructions of the shipment", default="")
    booking_number = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="Sealift Booking Number")
    username = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="ubbe creator username")
    email = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="ubbe creator email")
    requested_pickup_time = DateTimeField(
        help_text="The requested pickup start time", default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    requested_pickup_close_time = DateTimeField(
        help_text="The requested pickup end time", default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )
    estimated_delivery_date = DateTimeField(
        help_text="The requested pickup start time", default=datetime(year=1, month=1, day=1, tzinfo=timezone.utc)
    )

    is_food = BooleanField(default=False)
    is_dangerous_good = BooleanField(default=False)
    is_pharma = BooleanField(default=False)
    is_shipped = BooleanField(default=True, help_text="Is the shipment shipped, otherwise shipment is canceled(False).")
    is_delivered = BooleanField(default=False, help_text="Is the shipment delivered?")
    is_cancel = BooleanField(default=False, help_text="Has the shipment been requested to be cancelled.")
    is_cancel_completed = BooleanField(default=False, help_text="Has the shipment been cancelled by BBE Staff")

    class Meta:
        verbose_name = "Shipment"
        verbose_name_plural = "Shipments"

    @staticmethod
    def gen_id() -> str:
        return "{}{:010d}".format(GO_PREFIX, random.randint(0, 9999999999))

    def _origin_city(self):
        return "{} - {}, {}".format(self.origin.city, self.origin.province.code, self.origin.province.country.code)

    def _destination_city(self):
        return "{} - {}, {}".format(self.destination.city, self.destination.province.code,
                                    self.destination.province.country.code)

    def one_step_save(self, params: tuple, user: User, subaccount: SubAccount, origin: dict, destination: dict):

        p_leg = None
        m_leg = None
        d_leg = None
        ship_origin = Address.create_or_find(origin)
        ship_destination = Address.create_or_find(destination)
        mid_origin = Address.create_or_find(params[1]['origin'])
        mid_destination = Address.create_or_find(params[1]['destination'])

        self.user = user
        self.subaccount = subaccount
        self.markup = subaccount.markup.default_percentage
        self.origin = ship_origin
        self.destination = ship_destination
        self.sender = Contact.create_or_find(origin)
        self.receiver = Contact.create_or_find(destination)
        self.purchase_order = params[1].get("po_number", "")
        self.reference_one = params[1].get("reference_one", "")
        self.reference_two = params[1].get("reference_two", "")
        self.project = params[1].get("project", "")
        self.quote_id = params[1].get("quote_id", "")
        self.special_instructions = params[1].get("special_instructions", "")
        self.username = params[1].get("username", "")
        self.email = params[1].get("email", "")
        self.is_food = params[1].get("is_food", False)
        date = getkey(params[1], 'pickup.date', "0001-01-01")
        open_time = getkey(params[1], 'pickup.start_time', "00:00")
        close = getkey(params[1], 'pickup.end_time', "00:00")
        start = datetime.strptime("{}{}".format(date, open_time), '%Y-%m-%d%H:%M')
        self.requested_pickup_time = start.replace(tzinfo=timezone.utc)
        end = datetime.strptime("{}{}".format(date, close), '%Y-%m-%d%H:%M')
        self.requested_pickup_close_time = end.replace(tzinfo=timezone.utc)
        self.cost = Decimal("0.00")
        self.freight = Decimal("0.00")
        self.surcharge = Decimal("0.00")
        self.tax = Decimal("0.00")
        self.is_pharma = params[1].get("is_pharma", False)
        self.is_dangerous_good = params[1].get("is_dangerous_shipment", False)

        if 'promo_code' in params[1]:
            self.promo_code = params[1]["promo_code"]

        if 'insurance_amount' in params[1] and params[1]["insurance_amount"] > 0:
            self.insurance_amount = params[1]["insurance_amount"]

            insurance_cost = Decimal(self.insurance_amount) * Decimal("0.003")
            insurance_cost = insurance_cost if insurance_cost > Decimal("15.00") else Decimal("15.00")
            self.insurance_cost = insurance_cost.quantize(self._price_sig_fig)

        if 'broker' in params[1]:
            broker = params[1]["broker"]
            broker["name"] = broker["company_name"]
            self.broker_address = Address.create_or_find(broker)
            self.broker = Contact.create_or_find(broker)

        if 'billing' in params[1]:

            billing_a = Address.create_or_find(params[1]["billing"])
            billing_c = Contact.create_or_find(params[1]["billing"])
            self.billing = billing_a
            self.payer = billing_c

        if subaccount.is_bbe:

            if 'bc_customer_code' in params[1]:
                self.bc_customer_code = params[1]["bc_customer_code"]

            if 'bc_customer_name' in params[1]:
                self.bc_customer_name = params[1]["bc_customer_name"]

        else:
            self.bc_customer_code = subaccount.bc_customer_code
            self.bc_customer_name = subaccount.bc_customer_name

        self.save()

        if self.subaccount.is_account_id:
            try:
                self.generate_account_id()
                self.save()
            except Exception:
                pass

        if params[0]:
            first_destination = Address.create_or_find(params[0]['destination'])

            p_leg = Leg().one_step_save(params[0], ship_origin, first_destination, self.shipment_id + "P", self)

        m_leg = Leg().one_step_save(params[1], mid_origin, mid_destination, self.shipment_id + "M", self)

        if params[2]:
            d_leg = Leg().one_step_save(params[2], mid_destination, ship_destination, self.shipment_id + "D", self)

        Package.one_step_save(params[1]["packages"], self)

        if self.origin.province.country != self.destination.province.country:
            Commodity.one_step_save(shipment=self, commodities_json=params[1]["commodities"])

        return p_leg, m_leg, d_leg

    def update(self) -> None:
        new_data = self.leg_shipment.aggregate(Sum('cost'), Sum('freight'), Sum('surcharge'), Sum('tax'))

        if new_data["cost__sum"] is None:
            self.cost = Decimal("0")
        else:
            self.cost = Decimal(new_data["cost__sum"]).quantize(self._price_sig_fig)

        if new_data["freight__sum"] is None:
            self.freight = Decimal("0")
        else:
            self.freight = Decimal(new_data["freight__sum"]).quantize(self._price_sig_fig)

        if new_data["surcharge__sum"] is None:
            self.surcharge = Decimal("0")
        else:
            self.surcharge = Decimal(new_data["surcharge__sum"]).quantize(self._price_sig_fig)

        if new_data["tax__sum"] is None:
            self.tax = Decimal("0")
        else:
            self.tax = Decimal(new_data["tax__sum"]).quantize(self._price_sig_fig)

        self.save()

        if self.requested_pickup_time == self._default_date:
            pickup_date = self.creation_date
        else:
            pickup_date = self.requested_pickup_time

        pickup_data = {
            "date": pickup_date.strftime("%Y-%m-%d")
        }
        previous_leg = None
        final_est_date = None

        for leg in self.leg_shipment.all():
            country = leg.origin.province.country.code
            province = leg.origin.province.code

            if previous_leg:
                est_departure = DateUtility().new_next_business_day(
                    country_code=country, prov_code=province, in_date=previous_leg.estimated_delivery_date
                )

                pickup_data = {
                    "date": est_departure.strftime("%Y-%m-%d")
                }

            estimated_delivery_date, transit = DateUtility(pickup=pickup_data).get_estimated_delivery(
                transit=leg.transit_days, country=country, province=province
            )

            leg.estimated_delivery_date = estimated_delivery_date
            leg.updated_delivery_date = estimated_delivery_date
            leg.save()
            previous_leg = leg
            final_est_date = estimated_delivery_date

        if final_est_date:
            self.estimated_delivery_date = final_est_date
            self.save()

        if self.promo_code:
            try:
                discount = PromoCodeUtility().apply(promo_code=self.promo_code, pre_tax_cost=self.cost - self.tax)
                self.promo_code_discount = discount
                self.save()
            except ViewException as e:
                pass

    def create_context(self) -> dict:

        multiplier = (self.markup/100) + 1

        return {
            "shipment_id": self.shipment_id,
            "ff_number": self.ff_number,
            "creation_date": self.creation_date.strftime('%Y/%m/%d'),
            "owner": self.user.username,
            "reference_one": self.reference_one,
            "reference_two": self.reference_two,
            "surcharges": self.surcharge,
            "freight": self.freight,
            "tax": self.tax,
            "total": self.cost,
            "markup_surcharges": Decimal(self.surcharge * multiplier).quantize(self._price_sig_fig),
            "markup_freight": Decimal(self.freight * multiplier).quantize(self._price_sig_fig),
            "markup_tax": Decimal(self.tax * multiplier).quantize(self._price_sig_fig),
            "markup_total": Decimal(self.cost * multiplier).quantize(self._price_sig_fig),
            "markup": self.markup,
            "origin": {
                "company_name": self.sender.company_name,
                "name": self.sender.name,
                "phone": self.sender.phone,
                "email": self.sender.email,
                "address": self.origin.address,
                "address_two": self.origin.address_two,
                "city": self.origin.city,
                "province": self.origin.province.code,
                "country": self.origin.province.country.code,
                "postal_code": self.origin.postal_code
            },
            "destination": {
                "company_name": self.receiver.company_name,
                "name": self.receiver.name,
                "phone": self.receiver.phone,
                "email": self.receiver.email,
                "address": self.destination.address,
                "address_two": self.destination.address_two,
                "city": self.destination.city,
                "province": self.destination.province.code,
                "country": self.destination.province.country.code,
                "postal_code": self.destination.postal_code
            },
            "packages": [
                package.to_json()
                for package in self.package_shipment.all()
            ],
            "legs": [
                leg.to_json()
                for leg in self.leg_shipment.all()
            ]
        }

    @property
    def to_api_json(self):
        multiplier = (self.markup / 100) + 1

        ret = {
            "shipment_id": self.shipment_id,
            "account_number": self.subaccount.subaccount_number,
            "creation_date": self.creation_date.strftime('%Y/%m/%d'),
            "reference_one": self.reference_one,
            "reference_two": self.reference_two,
            "origin": {
                "company_name": self.sender.company_name,
                "name": self.sender.name,
                "phone": self.sender.phone,
                "email": self.sender.email,
                "address": self.origin.address,
                "address_two": self.origin.address_two,
                "city": self.origin.city,
                "province": self.origin.province.code,
                "country": self.origin.province.country.code,
                "postal_code": self.origin.postal_code
            },
            "destination": {
                "company_name": self.receiver.company_name,
                "name": self.receiver.name,
                "phone": self.receiver.phone,
                "email": self.receiver.email,
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
            "packages": [
                package.to_json()
                for package in self.package_shipment.all()
            ],
            "legs": [
                leg.to_api_json
                for leg in self.leg_shipment.all()
            ]
        }

        if self.user.username == "GoBox":
            ret["markup"] = self.markup

        return ret

    # TODO - Review save, believe this is causing duplicate/additional queries.
    def generate_account_id(self) -> None:
        """

            :return: None
        """
        try:
            # TODO - CITY ALIAS CHECK - BBE OR NEW AIRBASE SPECIFIC

            if self.origin.city.lower() == "calgary":
                city = "Calgary International Airport"
            else:
                city = self.origin.city

            airport = Airport.objects.get(name=city)
            code = airport.code
        except ObjectDoesNotExist as e:
            code = self.subaccount.id_prefix

        date = self.creation_date.strftime("%d%b%y")
        count = self.subaccount.id_counter
        account_id = f'{code}{date}-{count:03d}'

        self.account_id = account_id
        self.subaccount.id_counter += 1
        self.subaccount.save()

    # Override
    def save(self, *args, **kwargs) -> None:
        if len(self.shipment_id) == ID_LENGTH and self.shipment_id[0:2] == GO_PREFIX:
            self.clean_fields()
            self.validate_unique()
            super().save(*args, **kwargs)
            return None
        ship_id = self.gen_id()

        while Shipment.objects.filter(shipment_id=ship_id).exists():
            ship_id = self.gen_id()
        self.shipment_id = ship_id

        self.clean_fields()
        self.validate_unique()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< Shipment ({self.shipment_id}, {self.user.username}: {self.origin.city} to {self.destination.city}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.shipment_id}, {self.origin.city} to {self.destination.city}"
