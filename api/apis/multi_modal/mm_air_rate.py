import copy

import gevent

from api.apis.carriers.bbe.endpoints.bbe_rate_v1 import BBERate
from api.apis.carriers.union.api_union_v2 import Union
from api.apis.multi_modal.rate_api import RateAPI
from api.apis.services.airbase.airbase import FindAirbase
from api.apis.services.airbase.carrier_airbases.buffalo import BuffaloAirbase
from api.apis.services.airbase.carrier_airbases.cn_airbase import CanadianNorthAirbase
from api.exceptions.project import ViewException
from api.globals.carriers import CAN_NORTH, BBE, CAN_POST, BUFFALO_AIRWAYS, DAY_N_ROSS, ABF_FREIGHT


class MultiModalAirRate(RateAPI):

    def __init__(self, gobox_request: dict) -> None:
        super(MultiModalAirRate, self).__init__(gobox_request)

        self._air_carriers = []
        self._ground_carriers = []
        self._requests = []
        self._responses = []

        self._carrier_mids = {}

        self._first_leg_airbases = []
        self._last_leg_airbases = []
        self._pickup_addresses = []
        self._delivery_addresses = []
        self._pickup_requests = []
        self._delivery_requests = []
        self._main_requests = []
        self._pickup_responses = []
        self._delivery_responses = []
        self._main_responses = []
        self.carrier_list = []

    @staticmethod
    def _set_address(request: dict, key: str, airbase: dict):
        """
            Update Origin or Destination address information to port.
            :param request: rate request.
            :param key: Key to update, ex: "Origin"
            :param port: Port Object
            :return:
        """
        request[key]["address"] = copy.deepcopy(airbase["address"])
        request[key]["city"] = copy.deepcopy(airbase["city"])
        request[key]["company_name"] = "GoBox API"
        request[key]["country"] = copy.deepcopy(airbase["country"])
        request[key]["postal_code"] = copy.deepcopy(airbase["postal_code"])
        request[key]["province"] = copy.deepcopy(airbase["province"])
        request[key]["base"] = copy.deepcopy(airbase["base"])

    def _add_leg(self, pickup: dict, main: dict, delivery: dict, first: dict, last: dict):
        """
            Add yellowknife to requests if the middle airbase is Edmonton
            :param pickup: Pickup Request for YEG CN
            :param main: Main Request for YEG CN
            :param delivery: Delivery Request for YEG CN
            :return: None
        """
        pickup_leg = copy.deepcopy(pickup)
        main_leg = copy.deepcopy(main)
        delivery_leg = copy.deepcopy(delivery)

        main_leg["mid_o"] = first
        main_leg["mid_d"] = last

        # Update request params with airbase addresses
        self._set_address(request=pickup_leg, key="destination", airbase=first)
        self._set_address(request=main_leg, key="origin", airbase=first)
        self._set_address(request=main_leg, key="destination", airbase=last)
        self._set_address(request=delivery_leg, key="origin", airbase=last)

        # Add multi leg to list of requests
        self._requests.append((pickup_leg, main_leg, delivery_leg))

    def _build_buffalo(self, air_id: int, p_leg: dict, m_leg: dict, d_leg: dict, mid_origin, mid_destination):

        north = ["NT", "NU"]
        yzf_base = BuffaloAirbase().get_yellowknife()
        yeg_base = BuffaloAirbase().get_edmonton()

        o_province = self._origin["province"]
        d_province = self._destination["province"]

        # Set middle locations
        m_leg["mid_o"] = mid_origin
        m_leg["mid_d"] = mid_destination

        p_leg["carrier_id"] = self._ground_carriers
        m_leg["carrier_id"] = [air_id]
        d_leg["carrier_id"] = self._ground_carriers

        p_leg["is_pickup"] = True
        d_leg["is_delivery"] = True

        if o_province in north and d_province in north:
            self._build_other_air(
                air_id=air_id,
                p_leg=p_leg,
                m_leg=m_leg,
                d_leg=d_leg,
                mid_origin=mid_origin,
                mid_destination=mid_destination
            )
        else:
            self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=yeg_base, last=mid_destination)
            self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=yzf_base, last=mid_destination)

    def _build_canadian_north(self, air_id: int, p_leg: dict, m_leg: dict, d_leg: dict, mid_origin, mid_destination):
        """
            Create Air request for Canadian North.
            :param air_id: Carrier ID (int)
            :param p_leg: Pickup Leg (dict)
            :param m_leg: Main Leg (dict)
            :param d_leg: Delivery Leg (dict)
            :param mid_origin: Middle Location Origin (Airbase Object)
            :param mid_destination: Middle Location Destination (Airbase Object)
        """

        yzf_base = CanadianNorthAirbase().get_yellowknife()
        yeg_base = CanadianNorthAirbase().get_edmonton()
        yow_base = CanadianNorthAirbase().get_ottawa()

        # Set middle locations
        m_leg["mid_o"] = mid_origin
        m_leg["mid_d"] = mid_destination

        # Set Pickup Carriers
        if self._origin["province"] in ["NT", "NU"]:
            p_leg["carrier_id"] = [CAN_NORTH, BBE]
        else:
            p_leg["carrier_id"] = self._ground_carriers

        # Set Air Carriers
        m_leg["carrier_id"] = [air_id]

        # Set Delivery Carriers
        if self._destination["province"] in ["NT", "NU"]:
            d_leg["carrier_id"] = [CAN_NORTH, BBE]
        else:
            d_leg["carrier_id"] = self._ground_carriers

        p_leg["is_pickup"] = True
        d_leg["is_delivery"] = True

        west_provinces = ["BC", "AB", "SK", "YT"]
        east_provinces = ["NL", "PE", "NS", "NB", "ON"]
        north = ["NT", "NU"]

        o_province = self._origin["province"]
        o_postal_code = self._origin["postal_code"]
        d_province = self._destination["province"]
        d_postal_code = self._destination["postal_code"]

        if o_province in north and d_province in north:
            self._set_address(request=p_leg, key="destination", airbase=mid_origin)
            self._set_address(request=m_leg, key="origin", airbase=mid_origin)
            self._set_address(request=m_leg, key="destination", airbase=mid_destination)
            self._set_address(request=d_leg, key="origin", airbase=mid_destination)

            # # Add multi leg to list of requests
            self._requests.append((p_leg, m_leg, d_leg))
        else:
            is_yeg = False
            is_yzf = False
            is_yow = False

            if o_province in ["NT", "NU"]:

                if d_province in west_provinces:
                    # Destination Province is in the West
                    if o_province == "NT" or o_postal_code in ["X0B0C0", "X0B1J0", "X0B1K0", "X0B0E0", "X0C0G0", "X0B1B0"]:
                        # Origin Province is in the NT , Only show YEG and YZF options
                        is_yzf = True
                        is_yeg = True
                    else:
                        # Origin Province is in the NT , Show all Airbase options
                        is_yzf = True
                        is_yeg = True
                        is_yow = True
                else:
                    # Destination Province is in the East
                    if o_province == "NT" or o_postal_code in ["X0B0C0", "X0B1J0", "X0B1K0", "X0B0E0", "X0C0G0", "X0B1B0"]:
                        # Origin Province is in the NT , Show all Airbase options
                        is_yzf = True
                        is_yeg = True
                        is_yow = True
                    else:
                        # Origin Province is in the NU , Only show YOW option
                        is_yow = True

                if is_yeg:
                    self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=mid_origin, last=yeg_base)

                if is_yzf:
                    self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=mid_origin, last=yzf_base)

                if is_yow:
                    self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=mid_origin, last=yow_base)
            else:
                if o_province in west_provinces:
                    # Origin Province is in the West
                    if d_province == "NT" or d_postal_code in ["X0B0C0", "X0B1J0", "X0B1K0", "X0B0E0", "X0C0G0", "X0B1B0"]:
                        # Destination Province is in the NT , Only show YEG and YZF options
                        is_yzf = True
                        is_yeg = True
                    else:
                        # Destination Province is in the NU , Show all Airbase options
                        is_yzf = True
                        is_yeg = True
                        is_yow = True
                else:
                    # Origin Province is in the East
                    if d_province == "NT" or d_postal_code in ["X0B0C0", "X0B1J0", "X0B1K0", "X0B0E0", "X0C0G0", "X0B1B0"]:
                        # Destination Province is in the NT , Show all Airbase options
                        is_yzf = True
                        is_yeg = True
                        is_yow = True
                    else:
                        # Destination Province is in the NU , Only show YOW option
                        is_yow = True

                if is_yeg:
                    self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=yeg_base, last=mid_destination)

                if is_yzf:
                    self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=yzf_base, last=mid_destination)

                if is_yow:
                    self._add_leg(pickup=p_leg, main=m_leg, delivery=d_leg, first=yow_base, last=mid_destination)

    def _build_other_air(self, air_id: int, p_leg: dict, m_leg: dict, d_leg: dict, mid_origin, mid_destination):
        """
            Create Air request for carrier air id.
            :param air_id: Carrier ID (int)
            :param p_leg: Pickup Leg (dict)
            :param m_leg: Main Leg (dict)
            :param d_leg: Delivery Leg (dict)
            :param mid_origin: Middle Location Origin (Airbase Object)
            :param mid_destination: Middle Location Destination (Airbase Object)
        """

        # Set middle locations
        m_leg["mid_o"] = mid_origin
        m_leg["mid_d"] = mid_destination

        p_leg["carrier_id"] = self._ground_carriers
        m_leg["carrier_id"] = [air_id]
        d_leg["carrier_id"] = self._ground_carriers

        p_leg["is_pickup"] = True
        d_leg["is_delivery"] = True

        # Update request params with airbase addresses
        self._set_address(request=p_leg, key="destination", airbase=mid_origin)
        self._set_address(request=m_leg, key="origin", airbase=mid_origin)
        self._set_address(request=m_leg, key="destination", airbase=mid_destination)
        self._set_address(request=d_leg, key="origin", airbase=mid_destination)

        # Add multi leg to list of requests
        self._requests.append((p_leg, m_leg, d_leg))

    def _build_request(self):
        """
            Build air multi legs and determine airbases for them.
            :return: None
        """

        for air in self._air_carriers:

            # Split request into the three legs
            pickup_leg = copy.deepcopy(self._gobox_request)
            main_leg = copy.deepcopy(self._gobox_request)
            delivery_leg = copy.deepcopy(self._gobox_request)

            # Get airbases
            mid_origin, mid_destination = FindAirbase().get_airbase(
                carrier_id=air,
                origin=self._origin,
                destination=self._destination
            )

            if not mid_origin or not mid_destination:
                continue

            if air == CAN_NORTH:
                # Build Canadian North Request
                self._build_canadian_north(
                    air_id=air,
                    p_leg=pickup_leg,
                    m_leg=main_leg,
                    d_leg=delivery_leg,
                    mid_origin=mid_origin,
                    mid_destination=mid_destination
                )
            elif air == BUFFALO_AIRWAYS:
                # Build Buffalo Request
                self._build_buffalo(
                    air_id=air,
                    p_leg=pickup_leg,
                    m_leg=main_leg,
                    d_leg=delivery_leg,
                    mid_origin=mid_origin,
                    mid_destination=mid_destination
                )
            else:
                # Build All other carrier requests
                self._build_other_air(
                    air_id=air,
                    p_leg=pickup_leg,
                    m_leg=main_leg,
                    d_leg=delivery_leg,
                    mid_origin=mid_origin,
                    mid_destination=mid_destination
                )

    def _separate_carriers(self):
        """
            Separate the sealift carriers from ground carriers.
            :return: tuple of carrier lists
        """
        omit_carriers = [CAN_POST, DAY_N_ROSS, ABF_FREIGHT]

        for carrier in self._carrier_id:
            if carrier in self._sealift_list or carrier in omit_carriers:
                continue

            if carrier in self._air_list:
                self._air_carriers.append(carrier)
            else:
                self._ground_carriers.append(carrier)

    def _send_requests(self):
        pickup_threads = []
        main_threads = []
        delivery_threads = []
        bbe_rate = BBERate(ubbe_request=self._gobox_request).rate(is_quote=True)

        # TODO: DECIDE HOW TO REDUCE DUPLICATE GROUND CALLS
        for pickup_leg, main_leg, delivery_leg in self._requests:

            if not pickup_leg or not main_leg or not delivery_leg:
                # LOGGER.info("Incorrect build request")
                continue

            pickup_request = Union(pickup_leg)
            main_request = Union(main_leg)
            delivery_request = Union(delivery_leg)

            pickup_threads.append(gevent.Greenlet.spawn(pickup_request.rate))
            main_threads.append(gevent.Greenlet.spawn(main_request.rate))
            delivery_threads.append(gevent.Greenlet.spawn(delivery_request.rate))

        gevent.joinall(pickup_threads)
        gevent.joinall(main_threads)
        gevent.joinall(delivery_threads)

        max_length = max(len(pickup_threads), len(main_threads), len(delivery_threads))

        for i in range(0, max_length):
            p_rates = pickup_threads[i].get()
            m_rates = main_threads[i].get()
            d_rates = delivery_threads[i].get()

            if not m_rates:
                continue

            if not p_rates:
                p_rates = bbe_rate

            if not d_rates:
                d_rates = bbe_rate

            self._responses.append((p_rates, m_rates, d_rates))

    def rate(self) -> list:
        self._separate_carriers()

        if not self._air_carriers:
            raise ViewException(code="503", message="MMAIR: No Carriers", errors=[])

        self._build_request()

        if not self._requests:
            raise ViewException(code="504", message="MMAIR: Error building requests", errors=[])

        self._send_requests()

        if not self._responses:
            raise ViewException(code="505", message="MMAIR: Error Retrieving Rates", errors=[])

        return self._responses
