import copy
from datetime import datetime

import gevent
from django.db import connection
from django.db.models import Prefetch

from api.apis.carriers.bbe.endpoints.bbe_rate_v1 import BBERate
from api.apis.carriers.union.api_union_v2 import Union
from api.apis.multi_modal.rate_api import RateAPI
from api.exceptions.project import ViewException
from api.globals.carriers import NEAS, NSSI, MTS
from api.globals.project import LOGGER, getkey
from api.models import Port, SealiftSailingDates


class MultiModalSealiftRate(RateAPI):
    _appointment_delivery = 1

    def __init__(self, gobox_request: dict) -> None:
        super(MultiModalSealiftRate, self).__init__(gobox_request)
        self._requests = []
        self._responses = []

        self.carrier_list = []

    @staticmethod
    def _error(message: dict) -> None:
        """
            Format errot response
            :param message: Error message
            :return: raise exception
        """
        connection.close()
        raise ViewException(message)

    @staticmethod
    def _get_cargo_packing_station(carrier_id, port_code: str):

        if carrier_id == NEAS and port_code != "CHU":
            return {
                "company_name": "NEAS Cargo Service Center",
                "address": "950 Boul. Cadieux",
                "city": "Valleyfield",
                "province": "QC",
                "country": "CA",
                "postal_code": "J6T6L4",
                "base": port_code
            }
        elif carrier_id == NSSI:
            return {
                "company_name": "Arctic Consultants",
                "address": "10200 Rue Mirabeau",
                "city": "Montreal",
                "province": "QC",
                "country": "CA",
                "postal_code": "H1J1T6",
                "base": port_code
            }
        elif carrier_id == MTS:
            return {
                "company_name": "BBE Edmonton",
                "address": "1759 35 Ave E",
                "city": "Edmonton International Airport",
                "province": "AB",
                "country": "CA",
                "postal_code": "T9E0V6",
                "base": port_code
            }

        return {}

    def _separate_carriers(self, carriers: list) -> tuple:
        """
            Separate the sealift carriers from ground carriers.
            :param carriers:
            :return: tuple of carrier lists
        """
        ground_ltl_ftl_list = self._ltl_list + self._ftl_list
        sealift_carrier_list = []
        ground_carrier_list = []

        if not carriers:
            return sealift_carrier_list, ground_carrier_list

        for carrier in carriers:
            if carrier in self._sealift_list:
                sealift_carrier_list.append(carrier)
                continue

            if carrier in ground_ltl_ftl_list:
                ground_carrier_list.append(carrier)
                continue

        return sealift_carrier_list, ground_carrier_list

    @staticmethod
    def _set_address(request: dict, key: str, port: Port):
        """
            Update Origin or Destination address information to port.
            :param request: rate request.
            :param key: Key to update, ex: "Origin"
            :param port: Port Object
            :return:
        """
        request[key]["address"] = port.address.address
        request[key]["city"] = port.address.city
        request[key]["company_name"] = "GoBox API"
        request[key]["country"] = port.address.province.country.code
        request[key]["postal_code"] = port.address.postal_code
        request[key]["province"] = port.address.province.code
        request[key]["base"] = port.code

    def _build_request(self, sealift: list, ground: list):
        """
            Build rate requests for each sealift carrier including pickup requests.
            :param sealift: list of sealift carriers
            :param ground: list of ground carriers
        """
        for carrier in sealift:
            port_dict, ports = self._get_port(carrier_id=carrier)

            if not ports:
                continue

            for port_str in ports:
                port = port_dict[port_str]["port"]
                sailings = port_dict[port_str]["sailings"]

                leg_one = copy.deepcopy(self._gobox_request)
                leg_two = copy.deepcopy(self._gobox_request)

                leg_one["carrier_id"] = ground
                leg_two["carrier_id"] = [carrier]

                if 'carrier_options' in leg_one:
                    if self._appointment_delivery not in leg_one["carrier_options"]:
                        leg_one["carrier_options"].append(self._appointment_delivery)

                if self._gobox_request.get("is_packing", False):
                    cargo = self._get_cargo_packing_station(carrier_id=carrier, port_code=port.code)

                    if cargo:
                        leg_one["destination"] = cargo
                    else:
                        self._set_address(request=leg_one, key="destination", port=port)
                else:
                    self._set_address(request=leg_one, key="destination", port=port)

                self._set_address(request=leg_two, key="origin", port=port)

                leg_two["mid_o"] = port.to_json
                leg_two["mid_d"] = copy.deepcopy(leg_two["destination"])
                leg_two["mid_d"]["base"] = "BBE"
                leg_two["sailings"] = copy.deepcopy(sailings)

                self._requests.append((leg_one, leg_two))

    def _get_port(self, carrier_id: int) -> tuple:
        """
            Get the shipping from port for a carrier.
            :param carrier_id: Carrier Code
            :return: Port Object or none if none exists
        """
        ports = set()
        port_dict = {}

        try:
            date = getkey(self._gobox_request, 'pickup.date')
            pickup_date = datetime.strptime(date, "%Y-%m-%d").date()
        except Exception:
            pickup_date = datetime.today()

        if not pickup_date:
            pickup_date = datetime.today()

        if self._is_dg:
            sailing_dates = SealiftSailingDates.objects.select_related(
                "port__address__province__country"
            ).prefetch_related(
                Prefetch(
                    "port_destinations", queryset=Port.objects.select_related("address")
                ),
            ).filter(
                carrier__code=carrier_id,
                bbe_dg_cutoff__gte=pickup_date
            )
        else:
            sailing_dates = SealiftSailingDates.objects.select_related(
                "port__address__province__country"
            ).prefetch_related(
                Prefetch(
                    "port_destinations", queryset=Port.objects.select_related("address")
                ),
            ).filter(
                carrier__code=carrier_id,
                bbe_cargo_cutoff__gte=pickup_date
            )

        for sailing in sailing_dates:
            if sailing.port_destinations.filter(address__city=self._gobox_request["destination"].get("city", "")).exists():
                if self._is_dg:
                    date = sailing.bbe_dg_cutoff.strftime("%Y/%m/%d")
                else:
                    date = sailing.bbe_cargo_cutoff.strftime("%Y/%m/%d")

                if sailing.port.name in port_dict:
                    name = sailing.get_name_display() + " - " + date + ":" + sailing.name
                    port_dict[sailing.port.name]["sailings"].append(name)
                else:
                    name = sailing.get_name_display() + " - " + date + ":" + sailing.name
                    port_dict[sailing.port.name] = {
                        "port": sailing.port,
                        "sailings": [name]
                    }
                    ports.add(sailing.port.name)

        return port_dict, ports

    def _send_requests(self):
        """
            Perform Rate requests.
        """
        pickup_threads = []
        main_threads = []
        bbe_rate = BBERate(ubbe_request=self._gobox_request).rate(is_quote=True)

        for leg_one, leg_two in self._requests:

            if not leg_one or not leg_two:
                LOGGER.critical("Incorrect build request")
                continue

            leg_one_request = Union(leg_one)
            leg_two_request = Union(leg_two)

            pickup_threads.append(gevent.Greenlet.spawn(leg_one_request.rate))
            main_threads.append(gevent.Greenlet.spawn(leg_two_request.rate))

        gevent.joinall(pickup_threads)
        gevent.joinall(main_threads)

        max_length = max(len(pickup_threads), len(main_threads))

        for i in range(0, max_length):
            p_rates = pickup_threads[i].get()
            m_rates = main_threads[i].get()

            if not m_rates:
                continue

            self._responses.append((p_rates, m_rates, bbe_rate))

    def rate(self) -> list:
        sealift_carriers, ground_carriers = self._separate_carriers(carriers=self._carrier_id)

        if not sealift_carriers or not ground_carriers:
            self._error({"rate.mm_Sealift.error": "No Carriers"})

        self._build_request(sealift=sealift_carriers, ground=ground_carriers)

        if not self._requests:
            self._error({"rate.request.error": "Error building requests"})

        self._send_requests()

        if not self._responses:
            self._error({"rate.rate.error": "Error Retrieving Rates"})

        connection.close()
        return self._responses
