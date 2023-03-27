import datetime
from _decimal import Decimal, ROUND_HALF_UP

import copy

from zeep import CachingClient, Transport
from zeep.cache import InMemoryCache
from zeep.plugins import HistoryPlugin

from api.exceptions.project import ViewException
from api.globals.carriers import DAY_N_ROSS, SAMEDAY
from api.globals.project import DEFAULT_TIMEOUT_SECONDS
from api.models import CityNameAlias
from brain import settings
from brain.settings import DAYROSS_BASE_URL


class DayRossAPI:
    _dr_history = None
    _dr_client = None
    _dr_ns0 = None
    _url = DAYROSS_BASE_URL

    # DR api values
    _sig_fig = Decimal("0.01")
    _package_threshold = 6
    _length_unit = "Centimeters"
    _weight_unit = "Kilograms"
    _measurement_system = "Metric"
    _shipment_type = "Regular"
    _payment_type = "ThirdParty"
    _service_type = "C"
    _charge_codes = {
        "TRFAMT": "Freight",
        "TARIFF": "Freight",
        "FTAXLT": "Surcharge",
        "FSC-A": "Surcharge",
        "FSC-G": "Surcharge",
        "PRESDL": "Surcharge",
        "PRESPU": "Surcharge",
        "DANGER": "Surcharge",
        "NAVCN5": "Surcharge",
        "AIS": "Surcharge",
        "ONHST": "Tax",
        "GST": "Tax",
        "NBHST": "Tax",
        "NLHST": "Tax",
        "NSHST": "Tax",
        "HST": "Tax",
        "CWT": "Identifier",
        "ASLBS": "Identifier",
        "CHAS": "Identifier",
    }

    _delivery_appointment = 1
    _pickup_appointment = 2
    _tailgate = 3
    _heated_truck = 6
    _refrigerated_truck = 5
    _power_tailgate_pickup = 3
    _power_tailgate_delivery = 17
    _inside_pickup = 9
    _inside_delivery = 10

    _bbe_account = [
        "5edcc144-4546-423a-9fcd-2be2418e4720",  # BBE LIVE
        "b7d32b99-ce39-4629-bb2f-df9c93b1dcca",  # BBE Beta
        "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",  # BBE Ken Local
        "2c0148a6-69d7-4b22-88ed-231a084d2db9",  # Lloyd GN BEER
    ]

    def __init__(self, ubbe_request: dict):
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._expiry_date = datetime.datetime.today() + datetime.timedelta(weeks=1)
        self._carrier_id = self._ubbe_request["carrier_id"]
        self._sub_account = self._ubbe_request["objects"]["sub_account"]

        # Set up request
        self.create_connection()

        if self._carrier_id == DAY_N_ROSS:
            self._name = "Day & Ross"
            self._division = "GeneralFreight"
            self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                DAY_N_ROSS
            ]["account"]
        else:
            self._name = "Sameday"
            self._division = "Sameday"
            self._carrier_account = self._ubbe_request["objects"]["carrier_accounts"][
                SAMEDAY
            ]["account"]

        self._username = self._carrier_account.username.decrypt()
        self._password = self._carrier_account.password.decrypt()
        self._account_number = self._carrier_account.account_number.decrypt()

    @property
    def dr_history(self):
        return self._dr_history

    @property
    def dr_client(self):
        return self._dr_client

    @property
    def dr_ns0(self):
        return self._dr_ns0

    def _create_address(self, address: dict):
        """
        Create SOAP NS0 address object.
        :param address: dictionary object with address fields.
        :return:
        """

        city = CityNameAlias.check_alias(
            address["city"], address["province"], address["country"], self._carrier_id
        )
        postal_code = str(address["postal_code"]).replace(" ", "").upper()

        if self._carrier_id == DAY_N_ROSS:
            if postal_code == "T9E0V6":
                city = "Edmonton International Airport"

        return self._dr_ns0.ShipmentAddress(
            Address1=address["address"],
            Address2=address.get("address_two", ""),
            City=city,
            Country=address["country"],
            Name=address.get("name", ""),
            PostalCode=address["postal_code"],
            Province=address["province"],
            CompanyName=address["company_name"],
            EmailAddress="customerservice@ubbe.com",
            PhoneNumber=address.get("phone", ""),
        )

    def _create_items(self, packages: list) -> list:
        """

        :param packages:
        :return:
        """
        items = []

        for package in packages:
            quantity = package.get("quantity", 1)

            items.append(
                self._dr_ns0.ShipmentItem(
                    Length=int(Decimal(package["length"]).quantize(0, ROUND_HALF_UP)),
                    Width=int(Decimal(package["width"]).quantize(0, ROUND_HALF_UP)),
                    Height=int(Decimal(package["height"]).quantize(0, ROUND_HALF_UP)),
                    LengthUnit=self._length_unit,
                    Pieces=quantity,
                    Weight=int(Decimal(package["weight"]).quantize(0, ROUND_HALF_UP))
                    * quantity,
                    WeightUnit=self._weight_unit,
                    Description=package.get("description", "Piece"),
                )
            )
        return self._dr_ns0.ArrayOfShipmentItem(items)

    def _create_options_day_ross(self, data: dict) -> None:
        """
        Format options for shipment request.
        :param data:
        :return:
        """
        special_services = []

        if not self._ubbe_request["origin"].get("has_shipping_bays", True):
            special_services.append(self._dr_ns0.ShipmentSpecialService("PRESPU"))

        if not self._ubbe_request["destination"].get("has_shipping_bays", True):
            special_services.append(self._dr_ns0.ShipmentSpecialService("PRESDL"))

        for option in self._ubbe_request.get("carrier_options", []):
            if option not in [
                self._delivery_appointment,
                self._power_tailgate_pickup,
                self._power_tailgate_delivery,
                self._heated_truck,
                self._inside_delivery,
                self._refrigerated_truck,
            ]:
                raise ViewException(
                    {
                        "api.error.dr.options": f"Day Ross does not support option {option}"
                    }
                )

            if option in [self._delivery_appointment]:
                special_services.append(self._dr_ns0.ShipmentSpecialService("APTFGT"))
            elif option == self._inside_delivery:
                special_services.append(self._dr_ns0.ShipmentSpecialService("INSDLY"))
            elif option in [self._heated_truck, self._refrigerated_truck]:
                special_services.append(self._dr_ns0.ShipmentSpecialService("PROTEC"))
            elif option == self._power_tailgate_pickup:
                special_services.append(self._dr_ns0.ShipmentSpecialService("TLGPU"))
            elif option == self._power_tailgate_delivery:
                special_services.append(self._dr_ns0.ShipmentSpecialService("TLGDEL"))

        if self._ubbe_request.get("is_dangerous_shipment", False):
            special_services.append(self._dr_ns0.ShipmentSpecialService("DANGEROUS"))

        if special_services:
            data["SpecialServices"] = self._dr_ns0.ArrayOfShipmentSpecialService(
                special_services
            )

    def _create_options_same_day(self, data: dict) -> None:
        """
        Format options for shipment request.
        :param data:
        :return:
        """
        special_services = []

        for option in self._ubbe_request.get("carrier_options", []):
            if option not in [
                self._pickup_appointment,
                self._delivery_appointment,
                self._heated_truck,
            ]:
                raise ViewException(
                    {
                        "api.error.dr.options": f"Sameday does not support option {option}"
                    }
                )

            if option == self._pickup_appointment:
                special_services.append(self._dr_ns0.ShipmentSpecialService("APPTPU"))
            elif option == self._delivery_appointment:
                special_services.append(self._dr_ns0.ShipmentSpecialService("APPT"))
            elif option == self._heated_truck:
                special_services.append(self._dr_ns0.ShipmentSpecialService("HEAT"))

        if self._ubbe_request.get("is_dangerous_shipment", False):
            special_services.append(self._dr_ns0.ShipmentSpecialService("HAZARD"))

        if special_services:
            data["SpecialServices"] = self._dr_ns0.ArrayOfShipmentSpecialService(
                special_services
            )

    def _create_references(self):
        """
        Format reference numbers for shipment request.
        :return:
        """

        references = [self._ubbe_request["order_number"]]

        awb = self._ubbe_request.get("awb", "")

        if awb:
            references.append(awb)

        reference_one = self._ubbe_request.get("reference_one", "")

        if reference_one:
            references.append(reference_one)

        reference_two = self._ubbe_request.get("reference_two", "")

        if reference_two:
            references.append(reference_two)

        return self._dr_ns0.ArrayOfString(references)

    def _create_pickup(self):
        """
        Format pickup information for shipment request.
        :return:
        """
        # TODO - TIMEZONE SHIT HERE

        if not self._ubbe_request["pickup"]:
            return "", ""

        date = self._ubbe_request["pickup"]["date"]
        start = self._ubbe_request["pickup"]["start_time"]
        end = self._ubbe_request["pickup"]["end_time"]
        start_parts = start.split(":")
        end_parts = end.split(":")

        if self._ubbe_request.get("do_not_pickup", False):
            pick_update = datetime.datetime.combine(
                date, datetime.datetime.min.time()
            ) + datetime.timedelta(days=30)
        else:
            pick_update = datetime.datetime.combine(date, datetime.datetime.min.time())

        ready_time = pick_update.replace(
            hour=int(start_parts[0]),
            minute=int(start_parts[1]),
            second=0,
            microsecond=0,
        )
        close_time = pick_update.replace(
            hour=int(end_parts[0]), minute=int(end_parts[1]), second=0, microsecond=0
        )

        return ready_time.isoformat(), close_time.isoformat()

    def create_connection(self) -> None:
        """
        Create SOAP request history and client.
        """

        if settings.DEBUG:
            wsdl = "api/apis/carriers/day_ross_v2/wsdl/staging.wsdl"
        else:
            wsdl = "api/apis/carriers/day_ross_v2/wsdl/production.wsdl"

        self._dr_history = HistoryPlugin()
        self._dr_client = CachingClient(
            wsdl,
            transport=Transport(cache=InMemoryCache(), timeout=DEFAULT_TIMEOUT_SECONDS),
            plugins=[self._dr_history],
        )
        self._dr_ns0 = self.dr_client.type_factory("ns0")

    def set_connection(self, connection) -> None:
        """
        Set hisory, client, and ns0 values.
        :param connection:
        """
        self._dr_history = connection.dr_history
        self._dr_client = connection.dr_client
        self._dr_ns0 = connection.dr_ns0

    def get_purchase_surcharge(self) -> Decimal:
        """
        Calculate Purchase Surcharge for day ross shipment.
        ***** We anticipate to discontinue the surcharge by May 31, 2022. *****
        :return:
        """
        min_charge = Decimal("20.00")
        max_charge = Decimal("760.00")
        weight = self._ubbe_request["total_weight_imperial"]
        purchase_surcharge = (weight / Decimal("100")) * Decimal("1.80")

        if min_charge > purchase_surcharge:
            return min_charge
        elif purchase_surcharge > max_charge:
            return max_charge

        return purchase_surcharge
